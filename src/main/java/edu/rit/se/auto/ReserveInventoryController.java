package edu.rit.se.auto;

import org.rapidoid.annotation.Controller;
import org.rapidoid.annotation.POST;

import javax.inject.Inject;


/**
 * Controller for reserving inventory for recipes
 */
@Controller
public class ReserveInventoryController {

    @Inject
    private BinManager binManager;

    @POST("/reserve")
    public String salad(Order order) {
        return binManager.tomatoBins + "";
    }
}
