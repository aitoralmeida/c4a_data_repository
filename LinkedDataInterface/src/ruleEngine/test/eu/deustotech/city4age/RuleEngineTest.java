package eu.deustotech.city4age;

import com.hp.hpl.jena.ontology.OntModel;
import com.hp.hpl.jena.rdf.model.InfModel;
import com.hp.hpl.jena.rdf.model.Model;
import com.hp.hpl.jena.rdf.model.ModelFactory;
import com.hp.hpl.jena.reasoner.Reasoner;
import com.hp.hpl.jena.reasoner.ValidityReport;
import com.hp.hpl.jena.reasoner.rulesys.GenericRuleReasoner;
import com.hp.hpl.jena.reasoner.rulesys.Rule;
import com.hp.hpl.jena.util.FileManager;
import com.sun.javafx.util.Logging;
import de.fuberlin.wiwiss.d2rq.jena.ModelD2RQ;
import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import org.junit.experimental.theories.suppliers.TestedOn;


import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.StringWriter;
import java.util.List;
import java.util.logging.Level;
import java.util.logging.Logger;

import static org.junit.Assert.*;

/**
 * This is the test suite of RuleEngine Inference program to test if all is OK
 *
 * @author Rubén Mulero
 */
public class RuleEngineTest {

    private static final Logger LOGGER = Logger.getLogger( InferenceMain.class.getName() );

    private final OntModel finalResult = ModelFactory.createOntologyModel();
    private Model instances;
    private Reasoner myReasoner;

    @Before
    public void setUp() throws Exception {
        // We are going to load mapping and rules files.
        Model mapModel = FileManager.get().loadModel("./mapping.ttl");
        this.instances = new ModelD2RQ(mapModel, "http://www.morelab.deusto.es/ontologies/sorelcom#");
        this.myReasoner = new GenericRuleReasoner(Rule.rulesFromURL("file:./rules.txt"));
        this.myReasoner.setDerivationLogging(true);
    }

    @After
    public void tearDown() throws Exception {
        // Close the models
        instances.close();
        finalResult.close();
    }


    /**
     * Test if we have a valid mapping.ttl file loaded into instances.
     *
     */
    @Test
    public void testValidTtlFile() throws Exception {
        boolean res = false;
        if (this.instances.size() > 0 && this.instances.listStatements().hasNext()) {
            // The file has loaded data and has statements.
            res = true;
        }
        assertTrue(res);
    }

    /**
     * Test if rules are properly loaded
     *
     */
    @Test
    public void testValidRulesFile() throws Exception {
        boolean res = false;
        // We are going to load rules from file
        List<Rule> listOfRules = Rule.rulesFromURL("file:./rules.txt");
        if (listOfRules.size() > 0) {
            // There are rules loaded into the list, so the file contains valid rules
            res = true;
        }
        assertTrue(res);
    }

    /**
     * Test if an inference model produce any results
     *
     */
    @Test
    public void testIsEmpty() throws Exception {
        boolean res = false;
        InfModel inf = ModelFactory.createInfModel(this.myReasoner, this.instances);
        if (!inf.isEmpty()) {
            /// Inference is OK. Maybe we have new statements
            res = true;
        }
        assertTrue(res);
    }

    /**
     * Test if the new Inference Model is consistent.
     *
     */
    @Test
    public void testIsConsistent() throws Exception {
        boolean res = false;
        InfModel inf = ModelFactory.createInfModel(this.myReasoner, this.instances);
        if (!inf.isEmpty()) {
            ValidityReport validity = inf.validate();
            if (validity.isValid()) {
                // Our inference has been validated and we can say that is consistent based on new rules.
                res = true;
            }
        }
        assertTrue(res);
    }

    /**
     * Test if there are new statements based on loaded rule in the Reasoner
     *
     */
    @Test
    public void testNewStatements() throws Exception {
        boolean res = false;
        InfModel inf = ModelFactory.createInfModel(this.myReasoner, this.instances);
        if (!inf.isEmpty()) {
            // It returns True if empty
           res = !inf.getDeductionsModel().isEmpty();
        }
        assertTrue(res);
    }

    /**
     * Test is new infered data is uploaded into Fuseki server. To do this it is needed.
     *
     *          --> A Fuseki server runing in localhost int port 3030
     *          ---> A city4age dataset created into Fuseki Server
     *
     */
    @Test
    public void testUploadedData() throws Exception {
        boolean res = false;
        InfModel inf = ModelFactory.createInfModel(this.myReasoner, this.instances);
        final OntModel finalResult = ModelFactory.createOntologyModel();


        finalResult.add(this.instances);
        finalResult.add(inf.getDeductionsModel());
        // Set prefix map
        finalResult.setNsPrefixes(this.instances.getNsPrefixMap());
        finalResult.setNsPrefixes(inf.getDeductionsModel().getNsPrefixMap());

        // Converting final result to string and writ it
        StringWriter out = new StringWriter();
        finalResult.write(out, "RDF/XML");
        String result = out.toString();
        // Launch curl to upload or current knowledge into Fuseki
        ProcessBuilder p = new ProcessBuilder("curl", "-k", "-X", "POST", "--header", "Content-Type: application/rdf+xml",
                "-d", result, "http://localhost:3030/city4age/data");
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
                res = true;
            }else {
                System.err.println("Some error happened. Is Fuseki activated?");
            }
        }catch (IOException e) {
            e.printStackTrace();
        }

        // Asserting the result
        assertTrue(res);
    }

}