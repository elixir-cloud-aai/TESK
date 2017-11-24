package uk.ac.ebi.tsc.tesk.util;

/**
 * @author Ania Niewielska <aniewielska@ebi.ac.uk>
 */
public enum TaskView {
    MINIMAL("MINIMAL"), BASIC("BASIC"), FULL("FULL");

    private String value;

    TaskView(String value) {
        this.value = value;
    }

    public static TaskView fromString(String view) {
        for (TaskView item : TaskView.values()) {
            if (view.toUpperCase().equals(item.value)) {
                return item;
            }
        }
        return TaskView.MINIMAL;
    }
}
