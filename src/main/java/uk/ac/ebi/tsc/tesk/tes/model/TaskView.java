package uk.ac.ebi.tsc.tesk.tes.model;

/**
 * @author Ania Niewielska <aniewielska@ebi.ac.uk>
 *
 * All values of view parameter in
 * {@link uk.ac.ebi.tsc.tesk.tes.api.V1Api#getTask(String, String)}
 * and {@link uk.ac.ebi.tsc.tesk.tes.api.V1Api#listTasks(String, Long, String, String)}
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
