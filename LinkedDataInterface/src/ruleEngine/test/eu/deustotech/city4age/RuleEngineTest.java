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
import de.fuberlin.wiwiss.d2rq.jena.ModelD2RQ;
import org.junit.After;
import org.junit.Before;
import org.junit.Test;



import static org.junit.Assert.*;

/**
 * This is the test suite of RuleEngine Inference program to test if all is OK
 *
 * @author Rubén Mulero
 */
public class RuleEngineTest {

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
        //todo find a good solution to know if there are rules loaded
        assertTrue(true);
    }

    /**
     * Test if an infefence model produce any results
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
        InfModel inf = ModelFactory.createInfModel(this.myReasoner, this.instances);
        if (!inf.isEmpty()) {
            // It returns True if empty
           assertTrue(!inf.getDeductionsModel().isEmpty());
        }
    }

}