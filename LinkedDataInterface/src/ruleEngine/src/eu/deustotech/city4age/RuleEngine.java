package eu.deustotech.city4age;

import com.hp.hpl.jena.graph.Graph;
import com.hp.hpl.jena.ontology.OntModel;
import com.hp.hpl.jena.ontology.Ontology;
import com.hp.hpl.jena.query.*;
import com.hp.hpl.jena.rdf.model.*;
import com.hp.hpl.jena.reasoner.Reasoner;
import com.hp.hpl.jena.reasoner.ValidityReport;
import com.hp.hpl.jena.reasoner.rulesys.GenericRuleReasoner;
import com.hp.hpl.jena.reasoner.rulesys.Rule;
import com.hp.hpl.jena.sparql.util.NodeFactory;
import com.hp.hpl.jena.util.FileManager;

import com.hp.hpl.jena.vocabulary.RDF;
import com.sun.xml.internal.bind.v2.TODO;
import de.fuberlin.wiwiss.d2rq.jena.ModelD2RQ;
import de.fuberlin.wiwiss.d2rq.server.PageServlet;
import sun.rmi.runtime.Log;

import javax.xml.ws.http.HTTPException;
import java.io.*;
import java.lang.reflect.Array;
import java.net.UnknownHostException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Iterator;
import java.util.List;
import java.util.logging.FileHandler;
import java.util.logging.Level;
import java.util.logging.Logger;
import java.util.logging.SimpleFormatter;
import java.util.regex.Matcher;
import java.util.regex.Pattern;


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
    private OntModel oldOntModel = null;
    private String newLine;
    private Logger LOGGER;
    private static final String c4aBaseURI = "http://www.morelab.deusto.es/ontologies/city4age#";
    private static final String owlBaseURI = "http://www.w3.org/2002/07/owl#";
    private static final String dbpedia = "https://dbpedia.org/sparql";


    /**
     * The constructor of the class. Here is defined the parameters of this class.
     * There are two mapFiles to attach. It is important to use this two files for each schema of database
     *
     * @param pMapFile    The first mapFile of D2RQ generated map file.
     * @param pRulesFiles The rules file containig all needed rules
     * @param pLogger     A looger instance to log actions of this class.
     */
    public RuleEngine(String pMapFile, String pRulesFiles, Logger pLogger) {
        this.mapFile = pMapFile;
        this.rulesFile = pRulesFiles;
        this.LOGGER = pLogger;
        // Separation printing service
        this.newLine = System.getProperty("line.separator");
    }

    /**
     * The main execution method for this class. Here we are going to take loaded Mapping and Rules file to try
     * infer new statmenets based on saved data in database.
     * <p>
     * This method will extract and map all data into knowledge and then, use the loaded Rules to try to create
     * new statements.
     * <p>
     * If all the process works as intented and the new knowledge is valid with the actual Design of the Ontology
     * then this data will be uploaded into Fuseki server.
     *
     * @return True or false if the operation is done successfully.
     */
    public boolean inference() {
        boolean res = false;
        Model instances = null;
        // Loading mapModelFile from Path
        Model mapModel = FileManager.get().loadModel(this.mapFile);
        // Load rules defined by the user.
        List<Rule> listRules = Rule.rulesFromURL("file:" + this.rulesFile);
        // We check if we have usefull data
        if (!mapModel.isEmpty() && !listRules.isEmpty()) {
            instances = new ModelD2RQ(mapModel, c4aBaseURI);
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
                    finalResult.add(instances);
                    finalResult.add(inf.getDeductionsModel());
                    // Set prefix map
                    finalResult.setNsPrefixes(instances.getNsPrefixMap());
                    finalResult.setNsPrefixes(inf.getDeductionsModel().getNsPrefixMap());
                    // Obtaining knowledge from Geocities API about different cities to have a 5 star-based Ontology.
                    this.updateCityInformation(finalResult);
                    // Print current data structure to stdout
                    // this.printResults(finalResult, inf, finalResult.getBaseModel());
                    //Upload into Fuseki
                    if (this.oldOntModel == null || !this.checkAreEquals(this.oldOntModel, finalResult)) {
                        // If the base model is different (new data into DB) or if the inference model is different (new inference throught new rules
                        // Then we will upload all data to Fuseki
                        if (this.oldOntModel != null) {
                            this.oldOntModel.close();
                        }
                        this.oldOntModel = finalResult;
                        this.serve(finalResult);
                    } else {
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
                    LOGGER.severe("There are conflicts with inferred values. Check system err output");
                }
            } else {
                // There is a problem in the inference model
                System.err.println("Problems in the inference model, it returns a empty state");
                LOGGER.severe("The inference returns a empty state. May the rule reasoner is not working well " +
                        "or instances model is bad formed.");
            }
            // Closing Files.
            inf.close();
        } else {
            System.err.println(" The mapping file or the rules file are empty. Please check if they are OK.");
            LOGGER.severe("Mapping file or Rules file are empty. Check if they are valid.");
        }
        // Closing files
        mapModel.close();
        listRules.clear();
        return res;
    }

    /**
     * Upload Data into Fuseki server
     *
     * @param pModel Result model with all statements
     */
    private void serve(Model pModel) {
        // Convert pModel into a String to send it via curl
        StringWriter out = new StringWriter();
        pModel.write(out, "RDF/XML");
        // String result = out.toString();
        try {
            // Writing the output in a file
            // Creating a temp file
            File tempFile = File.createTempFile("./ruleEngineOutput", ".tmp");
            // Write the output in the tempfile
            BufferedWriter bw = new BufferedWriter(new FileWriter(tempFile));
            bw.write(out.toString());
            bw.close();
            // Launch curl to upload or current knowledge into Fuseki
            ProcessBuilder p = new ProcessBuilder("curl", "-k", "-X", "POST", "--header", "Content-Type: application/rdf+xml",
                    "-d", "@"+tempFile.getAbsolutePath(), "https://localhost:8443/city4age/data");
                    // This piece of code is used for server testing purposes
                    //"-d", "@"+tempFile.getAbsolutePath(), "http://localhost:8080/fuseki/city4age/data");
            System.out.println("Uploading new Knowledge to Fuseki......................\n");
            LOGGER.info("Uploading data to Fuseki server");
            // Execute our command
            final Process shell = p.start();
            // catch output and see if all is ok
            BufferedReader reader =
                    new BufferedReader(new InputStreamReader(shell.getInputStream()));
            StringBuilder builder = new StringBuilder();
            String line = null;
            while ((line = reader.readLine()) != null) {
                builder.append(line);
                builder.append(System.getProperty("line.separator"));
            }
            String output = builder.toString();
            if (output.length() > 0 && output.contains("count")) {
                // We have good response from the server
                System.out.println("Ok");
                // Logging successful uploading
                LOGGER.info("New data uploaded to Fuseki." + newLine + "Number of instances: " + pModel.size()
                        + newLine + "Graph data uploaded is: " + pModel.write(System.out, "N-TRIPLES"));

            } else {
                System.err.println("Some error happened. Is Fuseki activated? : " +output);
                LOGGER.severe("Data can not upload to Fuseki, check if Fuseki is activated: " + output);
            }
        } catch (IOException e) {
            LOGGER.severe("Fatal IO error detected in ProcessBuilder call");
            e.printStackTrace();
        }
    }

    /**
     * This method detects if the loaded knowledge has some city information and calls to external
     * Ontologies to link their data with the loaded knowledge.
     *
     * @param pFinalResult: The loaded and inferred knowledge.
     */
    private void updateCityInformation(OntModel pFinalResult) {
        // Defining the list of target cities to obtain desired information
        final List<String> places = Arrays.asList("lecce", "singapore", "madrid", "birmingham", "montpellier", "athens",
                "LECCE", "SINGAPORE", "MADRID", "BIRMINGHAM", "MONTPELLIER", "ATHENS");
        // Iterate loaded statements of the model.
        StmtIterator iter = pFinalResult.listStatements();
        try {
            while (iter.hasNext()) {
                Statement stmt = iter.next();
                // Obtain the data from resources
                Resource s = stmt.getSubject();
                Property p = stmt.getPredicate();
                RDFNode o = stmt.getObject();

                // Prepare some values for evaluations
                String sURI = new String();
                String pURI = new String();
                String oURI = new String();

                // Assing the values of the current statement
                if (s.isURIResource()) {
                    // We get the URI
                    sURI = s.getURI();
                } else if (s.isAnon()) {
                    System.out.print("blank");
                }
                if (p.isURIResource())
                    // We get the URI.
                    pURI = p.getURI();
                if (o.isURIResource()) {
                    // We get the URI
                    oURI = o.asResource().getURI();
                } else if (o.isAnon()) {
                    System.out.print("blank");
                } else if (o.isLiteral()) {
                    oURI = o.asLiteral().getString();           // Getting the literal value (city name)
                }

                if (sURI.equals(c4aBaseURI+"City") && pURI.equals("dbp:name") && oURI.toLowerCase().equals(places)) {
                    LOGGER.info("--> updateCityInformation: Searching information from city: "+oURI.toLowerCase());
                    // Obtaining aditional resources of external ontologies
                    this.obtainCityInformation(oURI.toLowerCase(), pFinalResult);
                }
            }
        }catch (Exception e) {
            // We are goingi to raise the default exception. It can be raised from the method obtainCityInformation
            LOGGER.severe("--> updateCityInformation: An error happened when trying to update city information: ");
            System.err.println("--> updateCityInformation: An error happened when trying to update city information: ");
            e.printStackTrace();
        } finally {
            if (iter != null) iter.close();
        }
    }

    /**
     * This method search in geocitties Ontology to obtain a valid URI containing the city information
     *
     * @param pCity The name of the city to search
     * @return A statmenet contianing the needed knowledge to link a city with its information
     */
    private void obtainCityInformation(String pCity, OntModel pModel) {

        // Making the call to geoname database
        //TODO put this url as a static final value at top of this file
        String query = "http://api.geonames.org/search?name_equals="+pCity+"&featureClass=P&type=rdf&&username=elektro";
        ProcessBuilder p = new ProcessBuilder("curl", "-X", "POST", query);
        try {
            System.out.println("Calling to geocities about city information from: "+pCity +"\n");
            LOGGER.info("--> obtainCityInformation: Calling to geocities to obtain information from: "+ pCity);
            // Execute our command
            final Process shell = p.start();
            // catch output and see if all is ok
            BufferedReader reader =
                    new BufferedReader(new InputStreamReader(shell.getInputStream()));
            StringBuilder builder = new StringBuilder();
            String line = null;
            // Filling with information the string builder list
            while ((line = reader.readLine()) != null) {
                // with the actual line we need to extract a defiend pattern
                if (line.contains("<gn:Feature rdf:about=") || line.contains("<rdfs:seeAlso rdf:resource=\"http://dbpedia.org/resour")) {
                    // Regex pattern to extract the needed URI
                    Pattern pattern = Pattern.compile("\"(.*?)\"");
                    Matcher matcher = pattern.matcher(line);
                    if (matcher.find()) {
                        // Obtaining the needed resource
                        Resource subject = pModel.getResource(c4aBaseURI+"City");
                        // Obtaining the needed property
                        Property predicate = pModel.getProperty("owl:sameAS");
                        // Adding the URIS (They are not literal)
                        Resource object = ResourceFactory.createResource(matcher.group(1));
                        // Creating the logical statement
                        //use add property
                        pModel.add(subject, predicate, object);
                    }else {
                        // we are only to save the problem, but not raise any error.
                        LOGGER.warning("--> obtainCityInformation: We found a possible resource but the Regex matcher" +
                                "is failing for some reason: "+line);
                    }
                }
            }
            //System.out.println("Call succeeded. The size of new statement is: "+listStatements.size());
            //LOGGER.info("Call successful. The size of new statements is: "+listStatements.size());
        } catch (IOException e) {
            LOGGER.severe("--> obtainCityInformation: Fatal IO error detected in ProcessBuilder call");
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
