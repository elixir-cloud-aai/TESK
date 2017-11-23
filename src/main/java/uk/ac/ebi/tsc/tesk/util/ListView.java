package uk.ac.ebi.tsc.tesk.util;

import java.util.Arrays;

/**
 * @author Ania Niewielska <aniewielska@ebi.ac.uk>
 */
public enum ListView {
    MINIMAL("MINIMAL"), BASIC("BASIC"), FULL("FULL");

    private String value;

    ListView(String value) {
        this.value = value;
    }

    public static ListView fromString(String view) {
        for (ListView item : ListView.values()) {
            if (view.toUpperCase().equals(item.value)) {
                return item;
            }
        }
        return ListView.MINIMAL;
    }
}
