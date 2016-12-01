package eu.deustotech.city4age;

import com.hp.hpl.jena.rdf.model.Model;
import com.hp.hpl.jena.reasoner.Reasoner;
import com.hp.hpl.jena.reasoner.rulesys.GenericRuleReasoner;
import com.hp.hpl.jena.reasoner.rulesys.Rule;
import com.hp.hpl.jena.util.FileManager;

import java.util.Timer;
import java.util.TimerTask;
import java.util.logging.Level;
import java.util.logging.Logger;


/**
 * This is the main execution of the RuleEngine Reasoner. Here, we use a Timer to executed some timed code every X time
 * The user must send a valid mapping.ttl file and a rules.txt file to be inferred by the reasoner.
 *
 *
 *
 *
 * @author Rubén Mulero
 */

public class InferenceMain {

    private static final Logger LOGGER = Logger.getLogger( InferenceMain.class.getName() );
    private static boolean run = true;


    public static void main(String[] args) {
        if (args.length > 0 && args[0].length() > 0 && args[0].contains(".ttl") &&
                args[1].length() > 0 && args[1].contains("rules")) {
            RuleEngine rEngine = new RuleEngine(args[0], args[1]);

            // Defining the default timerTask
            Timer timer = new Timer();

            TimerTask timerTask = new TimerTask() {
                public void run() {
                    if (run) {
                        run = rEngine.inference();
                    }else {
                        timer.cancel();
                        timer.purge();
                        LOGGER.log(Level.SEVERE, "The timer is forced to stop, there is problem in the code");
                        System.err.println("The timer stops due to some erros");
                    }
                }
            };
            // Decide if the program uses user defined time or system default.
            if (args.length >= 3 && args[2].length() > 0 && isLong(args[2])) {
                LOGGER.log( Level.FINE, "User entered a defined time interval. The value is --> {}", args[2]);
                System.out.print("Executing a time-defined TimerTask");
                timer.scheduleAtFixedRate(timerTask, 0, Long.parseLong(args[2])); // Setting user defined time.
            }else {
                LOGGER.log( Level.FINE, "Using default time interval");
                System.out.print("Executing default TimerTask");
                timer.scheduleAtFixedRate(timerTask, 0, 60000);                   // Setting default time.
            }
        }else{
            System.err.println("You need to provide a valid mapping.ttl file or rules.txt file");
            System.err.println("usage: java -jar ruleEngine.jar <validMappedFile.ttl> <rules.txt>");
        }
    }

    /**
     * A simple method to know if a user argument is an Long or not
     *
     * @param str Argument typed by the user
     * @return True or false if the argument is a Long or not.
     */

    public static boolean isLong(String str) {
        try {
            Long.parseLong(str);
            return true;
        } catch (NumberFormatException e) {
            return false;
        }
    }

}

