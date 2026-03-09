<%@ page import="java.io.*, java.util.*" %>
<%
    String logDir = System.getProperty("catalina.base") + "/logs/receipts/";
    File dir = new File(logDir);
    
    if(!dir.exists()) dir.mkdirs();
    File sample = new File(dir, "sample.txt");
    if(!sample.exists()) {
        try(PrintWriter pw = new PrintWriter(new FileWriter(sample))) {
            pw.println("SYSTEM SAMPLE RECEIPT");
            pw.println("---------------------");
            pw.println("Item: Demo Product");
            pw.println("Cost: $ 0");
            pw.println("---------------------");
        }
    }

    // --- CLEANER ---
    long now = System.currentTimeMillis();
    long ttl = 60 * 1000; // 1 minuto
    
    File[] files = dir.listFiles();
    if(files != null) {
        for(File f : files) {

            if(!f.getName().equals("sample.txt") && (now - f.lastModified() > ttl)) {
                f.delete();
            }
        }
    }

    String sid = request.getParameter("sid");
    String itemsJson = request.getParameter("items");
    
    if(sid != null && sid.matches("[a-zA-Z0-9]+")) {
        File receiptFile = new File(logDir + sid + ".log");
        try(PrintWriter writer = new PrintWriter(new FileWriter(receiptFile))) {
            writer.println("Kety & Tom's RECEIPT - " + new java.util.Date());
            writer.println("Session ID: " + sid);
            writer.println("--------------------------------");
            writer.println("Items Data: " + (itemsJson != null ? itemsJson : "None"));
            writer.println("--------------------------------");
        }
        out.print("OK");
    } else {
        response.setStatus(400);
        out.print("Bad Request");
    }
%>