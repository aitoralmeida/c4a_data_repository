package eu.deustotech.city4age;


import sun.rmi.runtime.Log;

import java.io.File;
import java.io.IOException;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Timer;
import java.util.TimerTask;
import java.util.logging.FileHandler;
import java.util.logging.Level;
import java.util.logging.Logger;
import java.util.logging.SimpleFormatter;


/**
 * This is the main execution of the RuleEngine Reasoner. Here, we use a Timer to executed some timed code every X time
 * The user must send a valid mapping.ttl file and a rules.txt file to be inferred by the reasoner.
 *
 * @author Rubén Mulero
 */

public class InferenceMain {

    private static boolean run = true;
    private static final long defaultTime = 172800000;           // 24h defined in milliseconds

    public static void main(String[] args) {
        if (args.length > 0 && args[0].length() > 0 && args[0].contains(".ttl") &&
                args[1].length() > 0 && args[1].contains("rules")) {

            // Initializing logging service
            Logger LOGGER = initLoginService();

            // Loading RuleEngine
            RuleEngine rEngine = new RuleEngine(args[0], args[1], LOGGER);
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
                        System.err.println("The timer stops due to some errors");
                    }
                }
            };
            // Decide if the program uses user defined time or system default.
            if (args.length >= 3 && args[2].length() > 0 && isLong(args[2])) {
                LOGGER.info("User entered a defined time interval. The value is --> {}" + args[2]);
                System.out.println("Executing a time-defined TimerTask of: " +args[2] + " milliseconds");
                timer.scheduleAtFixedRate(timerTask, 0, Long.parseLong(args[2])); // Setting user defined time.
            }else {
                LOGGER.info("Using default time interval");
                System.out.println("Executing DEFAULT TimerTask of: "+ defaultTime +" milliseconds");
                timer.scheduleAtFixedRate(timerTask, 0, defaultTime);
            }
        }else if (args.length == 1 && args[0].equals("-h")) {
            // The user entered a HELP VALUES
            System.out.println("To use this program you need to run the following command: \n\n" +
                    " $>  java -jar ruleEngine.jar <validMappedFile.ttl> <rules.txt> <OPTIONAL time in miliseconds> \n\n" +
                    "Where: \n" +
                    "      * validMappedFile: is a valid D2RQ mapping file to map data from database \n" +
                    "      * rules: is a valid file with Jena generic rules \n" +
                    "      * optional time: is a user defined time in miliseconds \n");
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

    /**
     * This method initializes a Logging File to store data into disk.
     *
     *
     * @return a Logger instance.
     */
    private static Logger initLoginService() {
        Date date = new Date();
        SimpleDateFormat dateFormat = new SimpleDateFormat("dd-MM-yyyy HH-mm-ss") ;
        Logger logger = Logger.getLogger("RuleEngine");
        // Logging File initialization
        try {
            // This block configure the logger with handler and formatter
            File directory = new File("log");
            if (! directory.exists()){
                directory.mkdir();
            }
            FileHandler fh = new FileHandler("./log/reasoner-" + dateFormat.format(date) +".log");
            logger.addHandler(fh);
            SimpleFormatter formatter = new SimpleFormatter();
            fh.setFormatter(formatter);
            // First logging initialization
            logger.info("Initialising logging service.......");
        } catch (SecurityException e) {
            e.printStackTrace();
        } catch (IOException e) {
            e.printStackTrace();
        }
        return logger;
    }
}