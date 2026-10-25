import java.util.Scanner;
import java.util.Random;

public class GuessGame {

    public static void main(String[] args) {

        Scanner sc = new Scanner(System.in);
        Random rand = new Random();

        int number = rand.nextInt(100) + 1;
        int guess = -1;

        System.out.println("Guess a number between 1 to 100");

        while (guess != number) {

            System.out.print("Enter your guess: ");

            if (sc.hasNextInt()) {
                guess = sc.nextInt();

                if (guess > number) {
                    System.out.println("Too High!");
                } else if (guess < number) {
                    System.out.println("Too Low!");
                } else {
                    System.out.println("Correct! You win 🎉");
                }

            } else {
                System.out.println("Enter valid number!");
                sc.next();
            }
        }

        sc.close();
    }
}