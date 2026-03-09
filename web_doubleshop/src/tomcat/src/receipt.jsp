<%@ page import="java.io.*" %>
<%
    String receiptId = request.getParameter("id");
    StringBuilder content = new StringBuilder();
    
    if(receiptId == null) receiptId = "sample.txt";

    String basePath = System.getProperty("catalina.base") + "/logs/receipts/";
    File file = new File(basePath + receiptId);

    if (file.exists() && !file.isDirectory()) {
        try (BufferedReader br = new BufferedReader(new FileReader(file))) {
            String line;
            while ((line = br.readLine()) != null) {
                content.append(line.replace("<","&lt;")).append("\n");
            }
        } catch (Exception e) {
            content.append("Error reading receipt.");
        }
    } else {
        String nodeName = System.getenv("HOSTNAME"); 
        content.append("Receipt not found or expired (TTL 60s).\n");
        content.append("File requested: " + receiptId + "\n");
    }
%>
<!DOCTYPE html>
<html>
<head>
    <title>Receipt Viewer</title>
    <style>body{background:#111;color:#111;;font-family:monospace;padding:20px;white-space:pre;}</style>
</head>
<body><%= content.toString() %></body>
</html>