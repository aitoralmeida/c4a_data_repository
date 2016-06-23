package eu.deustotech.city4age;

import com.hp.hpl.jena.ontology.OntModel;
import com.hp.hpl.jena.rdf.model.*;
import com.hp.hpl.jena.reasoner.Reasoner;
import com.hp.hpl.jena.reasoner.ValidityReport;
import com.hp.hpl.jena.reasoner.rulesys.GenericRuleReasoner;
import com.hp.hpl.jena.reasoner.rulesys.Rule;
import com.hp.hpl.jena.util.FileManager;
import de.fuberlin.wiwiss.d2rq.jena.ModelD2RQ;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.StringWriter;
import java.util.Iterator;


/**
 * RuleEnngine is a class that loads a D2RQ mapping.ttl file and infer loaded knowledge using a custom rules.txt file
 *
 * if new knowledge is inferred the results are uploaded to Fuseki to create a SPARQL endpoint
 *
 * @author Rubén Mulero
 *
 */

public class RuleEngine {


    private Model instances;
    private Integer execution = 0;

    public RuleEngine(String pMapFile) {
        // Load mapping file for the first time
        Model mapModel = FileManager.get().loadModel(pMapFile);
        this.instances = new ModelD2RQ(mapModel, "http://www.morelab.deusto.es/ontologies/sorelcom#");

    }

    public void inference() {
        // Create a new ontoloyModel
        final OntModel finalResult = ModelFactory.createOntologyModel();
        // Load rules defined by the user.
        Reasoner myReasoner = new GenericRuleReasoner(Rule.rulesFromURL("file:./rules.txt"));
        myReasoner.setDerivationLogging(true);        // Allow to getDerivation: return useful information.
        // Infer new instances using rules and our instances
        InfModel inf = ModelFactory.createInfModel(myReasoner, instances);
        if (!inf.isEmpty()) {
            // Check if new Model is consistent
            ValidityReport validity = inf.validate();
            if (validity.isValid()) {
                // Add new knowledge to the model.
                finalResult.add(this.instances);
                finalResult.add(inf.getDeductionsModel());
                // Set prefix map
                finalResult.setNsPrefixes(this.instances.getNsPrefixMap());
                finalResult.setNsPrefixes(inf.getDeductionsModel().getNsPrefixMap());
                // updated instances
                this.instances = finalResult.getBaseModel();
                this.printResults(finalResult, inf);
                //Upload into Fuseki
                if (inf.getDeductionsModel().size() > 0.0) {
                    this.serve(finalResult);
                }
            } else {
                // There are conflicts
                System.err.println("Conflicts");
                for (Iterator i = validity.getReports(); i.hasNext(); ) {
                    System.err.println(" - " + i.next());
                }
            }
        }
    }

    /**
     *
     * Upload Data into fuseki server
     *
     * @param pModel Result model with all statements
     */
    private void serve(Model pModel) {
        // Convert pModel into a String to send it via curl
        StringWriter out = new StringWriter();
        pModel.write(out, "RDF/XML");
        String result = out.toString();
        // Launch curl to upload or current knowledge into Fuseki
        ProcessBuilder p = new ProcessBuilder("curl","-X", "POST", "--header","Content-Type: application/rdf+xml",
                "-d", result, "http://localhost:8080/fuseki/city4age/data");
        try {
            System.out.println("Uploading new Knowledge to Fuseki......................");
            System.out.println("");
            // Execute our command
            final Process shell = p.start();
            // catch output and see if all is ok
            BufferedReader reader =
                    new BufferedReader(new InputStreamReader(shell.getInputStream()));
            StringBuilder builder = new StringBuilder();
            String line = null;
            while ( (line = reader.readLine()) != null) {
                builder.append(line);
                builder.append(System.getProperty("line.separator"));
            }
            String output = builder.toString();
            if (output.length() > 0 && output.contains("count")) {
                // We have good response from the server
                System.out.println("Ok");
            }else {
                System.err.println("Some error happened. Is Fuseki activated?");
            }
        }catch (IOException e) {
            e.printStackTrace();
        }
    }


    // todo this method is only for testing. Delete after finished.
    private void printResults(OntModel pOntology, InfModel pInf) {
        this.execution++;
        pOntology.write(System.out, "N-TRIPLES");
        System.out.println("========================================");
        System.out.println("Number of elements: "+ this.instances.size());
        System.out.println("Execution number :"+this.execution);

        System.out.println("Infered count list "+pInf.getDeductionsModel().size());
    }
}

// curl -X PUT -H "Content-Type: application/rdf+xml" -d @./knowledge.rdf http://localhost:3030/city4age/data

/* Another way to change this is by using SOH commands that are imppl in Fuseki bundle for example:

  s-put http://localhost:3030/ds/data default Data/books.ttl

  If our dataset is called /ds and we have bootks.ttl stored somewhere we can use it to send data to Fuseki.

  Maybe it is a good point to decide if use curl or SOH commands.



####################################################### Only for persistent data ##############################

  Update a good chance is convert our data in N-Triple format and use tbloader to load all our current data

    tdbloader --loc:MYDB postten.nt


   A more faster solution is user the second version of tdbloader
    tdbloader2 --loc /path/for/database input1.ttl input2.ttl ...


##################################################### An example of SPARQL call

curl -i -X POST -d 'SELECT ?subject ?predicate ?object WHERE {?subject ?predicate ?object} LIMIT 25' http://10.48.1.115:8080/fuseki/city4age/query --header "Content-Type: application/sparql-query"



 */
