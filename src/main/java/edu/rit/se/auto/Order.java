package edu.rit.se.auto;

/**
 * Represents a person's order to the system, requesting reserved ingredients
 */
public class Order {
    /**
     * Number of standard burgers
     * 1x bun, 1x patty, 1x lettuce, 1x tomato
     */
    public int standards;
    /**
     * Number of double burgers
     * 1x bun, 2x patty, 1x lettuce, 1x tomato
     */
    public int doubles;
    /**
     * Number of minimalist burgers
     * 1x bun, 1x patty
     */
    public int minimalists;
    /**
     * Number of salads
     * 2x lettuce, 2x tomato
     */
    public int salads;

    /**
     * Gets the number of buns in this order
     * @return the count
     */
    public int bunCount() {
        return standards + doubles + minimalists;
    }

    /**
     * Gets the number of patties in this order
     * @return the count
     */
    public int pattyCount() {
        return standards + 2 * doubles + minimalists;
    }

    /**
     * Gets the number of tomatoes in this order
     * @return the count
     */
    public int tomatoCount() {
        return standards + doubles + 2 * salads;
    }

    /**
     * Gets the number of lettuces in this order
     * @return the count
     */
    public int lettuceCount() {
        return standards + doubles + 2 * salads;
    }

    @Override
    public String toString() {
        return "<Order standards=" + standards +
                " doubles=" + doubles +
                " minimalists=" + minimalists +
                " salads=" + salads + ">";
    }
}
