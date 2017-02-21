package eu.deustotech.city4age;

import com.hp.hpl.jena.graph.Graph;
import com.hp.hpl.jena.ontology.OntModel;
import com.hp.hpl.jena.rdf.model.*;
import com.hp.hpl.jena.reasoner.Reasoner;
import com.hp.hpl.jena.reasoner.ValidityReport;
import com.hp.hpl.jena.reasoner.rulesys.GenericRuleReasoner;
import com.hp.hpl.jena.reasoner.rulesys.Rule;
import com.hp.hpl.jena.util.FileManager;
import de.fuberlin.wiwiss.d2rq.jena.ModelD2RQ;
import sun.rmi.runtime.Log;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.StringWriter;
import java.util.Iterator;
import java.util.List;
import java.util.logging.FileHandler;
import java.util.logging.Level;
import java.util.logging.Logger;
import java.util.logging.SimpleFormatter;


/**
 * RuleEnngine is a class that loads a D2RQ mapping.ttl file and infer loaded knowledge using a custom rules.txt file
 *
 * if new knowledge is inferred the results are uploaded to Fuseki to create a SPARQL endpoint
 *
 * @author Rubén Mulero
 *
 */

public class RuleEngine {


    private Integer execution = 0;
    private String rulesFile;
    private String mapFile;
    private String mapFile2;
    private OntModel oldOntModel = null;
    private String newLine;
    private Logger LOGGER;
    private static final String dbpedia = "http://dbpedia.org/sparql";


    /**
     * The constructor of the class. Here is defined the parameters of this class.
     * There are two mapFiles to attach. It is important to use this two files for each schema of database
     *
     *
     * @param pMapFile The first mapFile of D2RQ generated map file.
     * @param pMapFile2 The second maFile of D2RQ generated map file
     * @param pRulesFiles The rules file containig all needed rules
     * @param pLogger A looger instance to log actions of this class.
     */
    public RuleEngine(String pMapFile, String pMapFile2, String pRulesFiles, Logger pLogger) {
        this.mapFile = pMapFile;
        this.mapFile2 = pMapFile2;
        this.rulesFile = pRulesFiles;
        this.LOGGER = pLogger;
        // Separation printing service
        this.newLine = System.getProperty("line.separator");
    }

    /**
     * The main execution method for this class. Here we are going to take loaded Mapping and Rules file to try
     * infer new statmenets based on saved data in database.
     *
     * This method will extract and map all data into knowledge and then, use the loaded Rules to try to create
     * new statements.
     *
     * If all the process works as intented and the new knowledge is valid with the actual Design of the Ontology
     * then this data will be uploaded into Fuseki server.
     *
     *
     * @return True or false if the operation is done successfully.
     */

    public boolean inference() {
        boolean res = false;
        Model instances = null;
        Model instances2 = null;
        // Loading mapModelFile from Path
        Model mapModel = FileManager.get().loadModel(this.mapFile);
        Model mapModel2 = FileManager.get().loadModel(this.mapFile2);
        // Load rules defined by the user.
        List <Rule> listRules = Rule.rulesFromURL("file:" + this.rulesFile);
        // We check if we have usefull data
        if (!mapModel.isEmpty() && !mapModel2.isEmpty() && !listRules.isEmpty()) {
            instances = new ModelD2RQ(mapModel, "http://www.morelab.deusto.es/ontologies/sorelcom#");
            instances2 = new ModelD2RQ(mapModel2, "http://www.morelab.deusto.es/ontologies/sorelcom#");
            //Todo: Check if this work well and instances are not merging
            //Merge all instances in a single value
            instances.add(instances2);
            // Create a new ontoloyModel
            final OntModel finalResult = ModelFactory.createOntologyModel();
            // Creating the reasoner based on previously loaded rules
            Reasoner myReasoner = new GenericRuleReasoner(listRules);
            myReasoner.setDerivationLogging(true);        // Allow to getDerivation: return useful information.
            // Infer new instances using rules and our instances
            InfModel inf = ModelFactory.createInfModel(myReasoner, instances);
            if (!inf.isEmpty()) {
                // Check if new Model is consistent
                ValidityReport validity = inf.validate();
                if (validity.isValid()) {
                    // Add new knowledge to the model.
                    // Todo your need to ensure to test carefully this part. Use a debugger.
                    finalResult.add(instances);
                    finalResult.add(inf.getDeductionsModel());
                    // Set prefix map
                    finalResult.setNsPrefixes(instances.getNsPrefixMap());
                    finalResult.setNsPrefixes(inf.getDeductionsModel().getNsPrefixMap());

                    // TODO check if we can obtain all prefixes from 2º instances
                    finalResult.setNsPrefixes(instances2.getNsPrefixMap());



                    // TODO in this part, we are goingi to user our approach to obtain city data
                    this.obtainCityInformation(finalResult);




                    // updated instances
                    this.printResults(finalResult, inf, finalResult.getBaseModel());
                    //Upload into Fuseki
                    if (this.oldOntModel == null || !this.checkAreEquals(this.oldOntModel, finalResult)) {
                        // If the base model is different (new data into DB) or if the inference model is different (new inference throught new rules
                        // Then we will upload all data to Fuseki
                        if (this.oldOntModel != null) {
                            this.oldOntModel.close();
                        }
                        this.oldOntModel = finalResult;
                        this.serve(finalResult);
                    }else {
                        finalResult.close();
                    }
                    // The function works well, so we return a True state
                    res = true;
                } else {
                    // There are conflicts
                    System.err.println("Conflicts");
                    for (Iterator i = validity.getReports(); i.hasNext(); ) {
                        System.err.println(" - " + i.next());
                    }
                    LOGGER.severe("There are conflicts with infered values. Check system err output");
                }
            }else {
                // There is a problem in the inference model
                System.err.println("Problems in the inference model, it returns a empty state");
                LOGGER.severe("The inference returns a empty state. May the rule reasoner is not working well " +
                        "or instances model is bad formed.");
            }
            // Closing Files.
            inf.close();
        }else {
            System.err.println(" The mapping file or the rules file are empty. Please check if they are OK.");
            LOGGER.severe("Mapping file or Rules file are empty. Check if they are valid.");
        }
        // Closing files
        mapModel.close();
        mapModel2.close();
        listRules.clear();
        return res;
    }

    /**
     *
     * Upload Data into Fuseki server
     *
     * @param pModel Result model with all statements
     */
    private void serve(Model pModel) {
        // Convert pModel into a String to send it via curl
        StringWriter out = new StringWriter();
        pModel.write(out, "RDF/XML");
        String result = out.toString();
        // Launch curl to upload or current knowledge into Fuseki
        ProcessBuilder p = new ProcessBuilder("curl", "-k", "-X", "POST", "--header", "Content-Type: application/rdf+xml",
                "-d", result, "http://localhost:8080/fuseki/city4age/data");
        try {
            System.out.println("Uploading new Knowledge to Fuseki......................\n");
            LOGGER.info("Uploading data to Fuseki server");
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
                // Logging sucesfull uploading
                LOGGER.info("New data uploaded to Fuseki." + newLine + "Number of instances: " + pModel.size()
                        + newLine +"Graph data uploaded is: " + pModel.write(System.out, "N-TRIPLES"));

            }else {
                System.err.println("Some error happened. Is Fuseki activated?");
                LOGGER.severe("Data can not upload to Fuseki, check if Fuseki is activated: " +output);
            }
        }catch (IOException e) {
            LOGGER.severe("Fatal IO error detected in ProcessBuilder call");
            e.printStackTrace();
        }
    }




    // TODO use this to add new contents of city based on information of final results.


    private void obtainCityInformation(OntModel pFinalResult) {
        // TODO We need to iterate data and request to DBpedia city information
        // Alternative use Spotlight to discover data



        // Iterate over the data to extract city name

        String pCity = new String();



        // Defining the structure of the quey
        String query = "PREFIX dcterms: <http://dbpedia.org/resource/>\n" +
                "\n" +
                "SELECT ?place WHERE{\n" +
                "  ?place owl:sameAs dcterms:"+ pCity + " .\n" +
                "  \n" +
                "}";


        ProcessBuilder p = new ProcessBuilder("curl", "-G", dbpedia, "--data-urlencode", "query='", query, "'");
        try{
            System.out.println("Requesting information from DBPedia\n");
            LOGGER.info("Making a call to DBPedia requesting information for " +pCity);
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
            String output = builder.toString(); // We rexeive the URI of the town

            // Decide here if append or not data





        }catch (IOException e) {
            LOGGER.severe("Fatal IO error detected in ProcessBuilder call");
            e.printStackTrace();
        }

    }

    /**
     * Checks if the ouputs of two diferent OntoModels are or not different.
     *
     * This is usefull to know if there is some new data in DB or if there are new Rules defined and we need to
     * upload data to a server.
     *
     * @param oldOntModel The Old Ontology Model
     * @param newOntModel The new Ontology Model
     * @return True if the Ontology's are equal or False if they are different.
     */
    private boolean checkAreEquals(Model oldOntModel, Model newOntModel) {
        boolean res = false;
        StringWriter oldOut = new StringWriter();
        StringWriter newOut = new StringWriter();
        oldOntModel.write(oldOut, "RDF/XML");
        newOntModel.write(newOut, "RDF/XML");
        if (oldOut.toString().equals(newOut.toString())) {
            res = true;
        }
        return res;
    }

    /**
     * Prints the actual knowledge with the actual execution number and what new statements are created with
     * ruleEngine
     *
     *
     * @param pOntology The actual knowledge ( Base + inferred)
     * @param pInf: The list containing the inferred elements.
     */
    private void printResults(OntModel pOntology, InfModel pInf, Model pInstances) {
        this.execution++;
        pOntology.write(System.out, "N-TRIPLES");
        System.out.println("========================================");
        System.out.println("Number of elements: "+ pInstances.size());
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

curl -k -i -X POST -d 'SELECT ?subject ?predicate ?object WHERE {?subject ?predicate ?object} LIMIT 25' http://10.48.1.115:8080/fuseki/city4age/query --header "Content-Type: application/sparql-query"



 */
