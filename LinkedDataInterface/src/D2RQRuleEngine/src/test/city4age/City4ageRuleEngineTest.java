package test.city4age;

import java.io.File;

import com.hp.hpl.jena.rdf.model.InfModel;
import com.hp.hpl.jena.rdf.model.Model;
import com.hp.hpl.jena.rdf.model.ModelFactory;
import com.hp.hpl.jena.rdf.model.Statement;
import com.hp.hpl.jena.rdf.model.impl.StmtIteratorImpl;
import com.hp.hpl.jena.reasoner.Reasoner;
import com.hp.hpl.jena.reasoner.rulesys.GenericRuleReasoner;
import com.hp.hpl.jena.reasoner.rulesys.Rule;
import com.hp.hpl.jena.util.iterator.ExtendedIterator;
import com.hp.hpl.jena.util.iterator.Filter;


import org.junit.Test;
import org.junit.After;
import org.junit.Before;

import static org.junit.Assert.*;

/**
 * Test Rule engine execution
 *
 * @author Rubén Mulero
 */
public class City4ageRuleEngineTest {

    private String absolute_path;
    private Model instancesRead;
    private Model instancesSave;

    @Before
    public void setUp() throws Exception {
        File execution_path = new File(".").getCanonicalFile();
        File relative_dest = new File(execution_path, "../../ruleEngine");
        absolute_path = relative_dest.getCanonicalPath();
        //Read input and ouptud data
        instancesRead = ModelFactory.createDefaultModel();
        instancesSave = ModelFactory.createDefaultModel();
    }

    @After
    public void tearDown() throws Exception {
        instancesRead.close();
        instancesSave.close();
    }

    /**
     *
     * Vamos a probar. Si se lee bien el fichero.
     * Si se guarda correctamnete.
     * Si se infieren nuevos métodos o no.
     */


    /**
     * Test if exist Any data in dataset.txt file
     *
     * @throws Exception
     */
    @Test
    public void loadFileTest() throws Exception {
        instancesRead.read("file:"+ absolute_path +"/dataset.txt", "TURTLE");
        // if instances contains data, this returns False. Looks good.
        assertFalse(instancesRead.isEmpty());
    }


    /**
     * Test if program saves output file in the system with data
     *
     * @throws Exception
     */

    @Test
    public void saveFileTest() throws Exception {
        instancesSave.read("file:"+ absolute_path +"/mapping.ttl", "TURTLE");
        // if instances contains data, this returns False. Looks good.
        assertFalse(instancesSave.isEmpty());
    }


    /**
     *Test if the Reasoner generated new statements based on our rules.txt file
     *
     * @throws Exception
     */
    @Test
    public void newInferedMethods() throws Exception {
        instancesRead.read("file:"+ absolute_path +"/dataset.txt", "N3");
        Reasoner myReasoner = new GenericRuleReasoner(Rule.rulesFromURL("file:"+ absolute_path +"/rules.txt"));
        myReasoner.setDerivationLogging(true);
        InfModel inf = ModelFactory.createInfModel(myReasoner, instancesRead);
        ExtendedIterator<Statement> stmts = inf.listStatements().filterDrop(new Filter<Statement>() {
            @Override
            public boolean accept(Statement o) {
                return instancesRead.contains(o);
            }
        });
        Model deductions = ModelFactory.createDefaultModel().add( new StmtIteratorImpl(stmts));
        if (deductions.getGraph().size() > 0) {
            // We have some new statements
            assertTrue(true);
        }else {
            assertTrue(false);
        }
        deductions.close();
        stmts.close();
    }

    /**
     * Test if loaded file and stored file contains different data
     *
     */
    @Test
    public void compareFiles() throws Exception {
        instancesRead.read("file:"+ absolute_path +"/dataset.txt", "TURTLE");
        instancesSave.read("file:"+ absolute_path +"/mapping.ttl", "TURTLE");
        assertNotSame(instancesRead, instancesSave);
    }
}