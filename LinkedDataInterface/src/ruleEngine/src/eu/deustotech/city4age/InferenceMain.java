package eu.deustotech.city4age;

import java.util.Timer;
import java.util.TimerTask;


/**
 * Main execution class. Here we create a timer to infer our knowledge ever X seconds
 *
 *
 * @author Rubén Mulero
 */

public class InferenceMain {

    public static void main(String[] args) {


        if (args.length > 0 && args[0].length() > 0 && args[0].contains(".ttl")) {
            //todo:::: we need to open file and see if arguments and prefixes are ok???
            //todo maybe is very interesting to load file from program rather than arguments.

            RuleEngine rEngine = new RuleEngine(args[0]);
            TimerTask timerTask = new TimerTask() {
                public void run() { rEngine.inference(); }
            };
            Timer timer = new Timer();
            //timer.scheduleAtFixedRate(timerTask, 0, 60000);
            timer.scheduleAtFixedRate(timerTask, 0, 10000);
        }else{
            System.err.println("You need to provide a valid mapping.ttl file");
            System.err.println("usage: java -jar reasoner.jar <validMappedFile.ttl>");
        }

    }
}

