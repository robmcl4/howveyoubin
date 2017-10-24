package edu.rit.se.auto;

import org.rapidoid.jdbc.JDBC;
import org.rapidoid.log.Log;

import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;

/**
 * Stores and Recalls the number of bins available for each ingredient
 */
public class BinManager {

    public int bunBins = 0,
               pattyBins = 0,
               lettuceBins = 0,
               tomatoBins = 0;

    public BinManager() {
        try {
            this.refreshBinCount();
        } catch (SQLException ex) {
            Log.warn(ex.getMessage());
            Log.warn("Failed to initialize bin counts, assuming zeroes");
        }
    }



    /**
     * Query the database to refresh our understanding of the bin count
     */
    private synchronized void refreshBinCount() throws SQLException {
        //
        // Using serialized transaction isolation level (which does locking reads)
        // ask for the size of each fragments table USING THE EXPECTED ORDERING to avoid deadlock
        //
        Log.info("Refreshing bin counts");
        Connection cxn = JDBC.getConnection();
        cxn.setAutoCommit(false);
        try {
            cxn.setTransactionIsolation(Connection.TRANSACTION_SERIALIZABLE);

            ResultSet rs = cxn.prepareStatement("SELECT COUNT(*) FROM bun_bins").executeQuery();
            rs.next();  // advance the result set onto the first result :(
            this.bunBins = rs.getInt(1);
            rs.close();

            rs = cxn.prepareStatement("SELECT COUNT(*) FROM patty_bins").executeQuery();
            rs.next();
            this.pattyBins = rs.getInt(1);
            rs.close();

            rs = cxn.prepareStatement("SELECT COUNT(*) FROM lettuce_bins").executeQuery();
            rs.next();
            this.lettuceBins = rs.getInt(1);
            rs.close();

            rs = cxn.prepareStatement("SELECT COUNT(*) FROM tomato_bins").executeQuery();
            rs.next();
            this.tomatoBins = rs.getInt(1);
            rs.close();
        } finally {
            cxn.commit();
        }
    }
}
