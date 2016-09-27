package eu.deustotech.city4age;

import java.util.Timer;
import java.util.TimerTask;
import java.util.logging.Level;
import java.util.logging.Logger;


/**
 * Main execution class. Here we create a timer to infer our knowledge ever X seconds
 *
 *
 * @author Rubén Mulero
 */

public class InferenceMain {

    private static final Logger LOGGER = Logger.getLogger( InferenceMain.class.getName() );

    public static void main(String[] args) {
        if (args.length > 0 && args[0].length() > 0 && args[0].contains(".ttl") &&
                args[1].length() > 0 && args[1].contains("rules")) {
            RuleEngine rEngine = new RuleEngine(args[0], args[1]);
            TimerTask timerTask = new TimerTask() {
                public void run() { rEngine.inference(); }
            };
            Timer timer = new Timer();
            //timer.scheduleAtFixedRate(timerTask, 0, 60000);
            if (args.length >= 3 && args[2].length() > 0 && isLong(args[2])) {
                LOGGER.log( Level.FINE, "User entered a defined time interval. The value is --> {}", args[2]);
                System.out.println("BLEBLLEL");
                timer.scheduleAtFixedRate(timerTask, 0, Long.parseLong(args[2])); // Setting user defined time.
            }else {
                LOGGER.log( Level.FINE, "Using default time interval");
                timer.scheduleAtFixedRate(timerTask, 0, 10000);                   // Setting default time.
            }
        }else{
            System.err.println("You need to provide a valid mapping.ttl file");
            System.err.println("usage: java -jar reasoner.jar <validMappedFile.ttl>");
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

