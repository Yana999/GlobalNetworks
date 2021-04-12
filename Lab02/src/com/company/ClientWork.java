package com.company;
import java.io.BufferedInputStream;
import java.io.BufferedOutputStream;
import java.io.BufferedReader;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.FileReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.PrintWriter;
import java.net.ServerSocket;
import java.net.Socket;
import java.util.ArrayList;
import java.util.HashMap;

public class ClientWork extends Thread
{

    private boolean debugMode = true;

    private enum transferType {
        ASCII, BINARY
    }

    private enum userStatus {
        NOTLOGGEDIN, ENTEREDUSERNAME, LOGGEDIN
    }

    // Path information
    private final String root;
    private String currentDirectory;
    private final String fileSeparator = "/";

    // control connection
    private Socket controlSocket;
    private PrintWriter controlOutWriter;
    private BufferedReader controlIn;


    // data Connection
    private ServerSocket dataSocket;
    private Socket dataConnection;
    private PrintWriter dataOutWriter;
    private int dataPort;
    private transferType transferMode = transferType.ASCII;


    // user
    private userStatus currentUserStatus = userStatus.NOTLOGGEDIN;
    private HashMap<String, String> users = new HashMap<>();
    private String currentUser = "";
    private ArrayList<String> anonymousUsers = new ArrayList<>();
    private final String anonymous = "anonymous";

    private boolean quitCommandLoop = false;

    public ClientWork(Socket client, int dataPort)
    {
        super();
        this.controlSocket = client;
        this.dataPort = dataPort;
        this.currentDirectory = System.getProperty("user.dir") + "/test";
        this.root = System.getProperty("user.dir");
        users.put("yana", "network");
    }

    public void run()
    {

        try
        {
            // Input from client
            controlIn = new BufferedReader(new InputStreamReader(controlSocket.getInputStream()));

            // Output to client, automatically flushed after each print
            controlOutWriter = new PrintWriter(controlSocket.getOutputStream(), true);

            // Greeting
            sendMessage("220 Welcome to the FTP-Server");

            // Get new command from client
            while (!quitCommandLoop)
            {
                executeCommand(controlIn.readLine());
            }

        }
        catch (Exception e)
        {
            e.printStackTrace();
        }
        finally
        {
            // Clean up
            try
            {
                controlIn.close();
                controlOutWriter.close();
                controlSocket.close();
                debugOutput("Sockets closed and worker stopped");
            }
            catch(IOException e)
            {
                e.printStackTrace();
                debugOutput("Could not close sockets");
            }
        }

    }

    private void executeCommand(String c)
    {
        // split command and arguments
        int index = c.indexOf(' ');
        String command = ((index == -1)? c.toUpperCase() : (c.substring(0, index)).toUpperCase());
        String args = ((index == -1)? null : c.substring(index+1, c.length()));


        debugOutput("Command: " + command + " Args: " + args);

        // The following commands specify access control identifiers
        switch(command) {
            case "USER":
                //USER NAME
                user(args);
                break;

            case "PASS":
                //PASSWORD
                pass(args);
                break;

            case "CWD":
                //CHANGE WORKING DIRECTORY
                сwd(args);
                break;

            case "LIST":
                //LIST
                if(args == null){

                }
                nlst(args);
                break;

            case "NLST":
                //NAME LIST
                nlst(args);
                break;

            case "PWD":
                //PRINT WORKING DIRECTORY
                pwd();
                break;

            case "QUIT":
                //LOGOUT
                quit();
                break;

            case "PASV":
                // PASSIVE
                pasv();
                break;

            case "SYST":
                //SYSTEM
                syst();
                break;

            case "PORT":
                //DATA PORT
                port(args);
                break;


            case "RETR":
                //RETRIEVE

                retr(args);
                break;

            case "MKD":
                //MAKE DIRECTORY
                if(!currentUser.equals(anonymous)) {
                    mkd(args);
                }else{
                    sendMessage("550 Not enough privileges.");
                }
                break;

            case "RMD":
                //REMOVE DIRECTORY
                if(!currentUser.equals(anonymous)) {
                    rmd(args);
                }else{
                    sendMessage("550 Not enough privileges.");
                }
                break;

            case "TYPE":
                //REPRESENTATION TYPE
                type(args);
                break;

            case "STOR":
                //STORE
                if(!currentUser.equals(anonymous)) {
                    stor(args);
                }else{
                    sendMessage("550 Not enough privileges.");
                }
                break;

            case "CDUP":
                //Change to the parent of the current working directory.
                сwd("..");
                break;

            default:
                sendMessage("Unknown command");
                break;

        }

    }

    private void sendMessage(String message)
    {
        controlOutWriter.println(message);
    }


    private void sendDataMessage(String message)
    {
        if (dataConnection == null || dataConnection.isClosed())
        {
            sendMessage("425 No data connection was established");
            debugOutput("Cannot send message, because no data connection is established");
        }
        else
        {
            dataOutWriter.print(message + '\r' + '\n');
        }

    }


    private void openDataConnectionPassive(int port)
    {

        try
        {
            dataSocket = new ServerSocket(port);
            dataConnection = dataSocket.accept();
            dataOutWriter = new PrintWriter(dataConnection.getOutputStream(), true);
            debugOutput("Data connection - Passive Mode - established");

        } catch (IOException e)
        {
            debugOutput("Could not create data connection.");
            e.printStackTrace();
        }

    }


    private void openDataConnectionActive(String ipAddress, int port)
    {
        try
        {
            dataConnection = new Socket(ipAddress, port);
            dataOutWriter = new PrintWriter(dataConnection.getOutputStream(), true);
            debugOutput("Data connection - Active Mode - established");
        } catch (IOException e)
        {
            debugOutput("Could not connect to client data socket");
            e.printStackTrace();
        }

    }


    private void closeDataConnection()
    {
        try
        {
            dataOutWriter.close();
            dataConnection.close();
            if (dataSocket != null)
            {
                dataSocket.close();
            }


            debugOutput("Data connection was closed");
        } catch (IOException e)
        {
            debugOutput("Could not close data connection");
            e.printStackTrace();
        }
        dataOutWriter = null;
        dataConnection = null;
        dataSocket = null;
    }


    private void user(String username)
    {
        if (users.keySet().contains(username.toLowerCase()))
        {
            sendMessage("331 User name okay, need password");
            currentUserStatus = userStatus.ENTEREDUSERNAME;
            currentUser = username.toLowerCase();
        }
        else if (currentUserStatus == userStatus.LOGGEDIN)
        {
            sendMessage("530 User already logged in");
        }
        else if(username.toLowerCase().equals(anonymous)){
            sendMessage("331 User name okay, need password");
            currentUserStatus = userStatus.ENTEREDUSERNAME;
            currentUser = username.toLowerCase();
            currentDirectory = System.getProperty("user.dir") + "/shared";
        }else
        {
            sendMessage("530 Not logged in");
        }
    }


    private void pass(String password)
    {
        // User has entered an anonymous
        if(currentUserStatus == userStatus.ENTEREDUSERNAME && currentUser.equals(anonymous)){
            currentUserStatus = userStatus.LOGGEDIN;
            sendMessage("230-Welcome");
            sendMessage("230 User logged in successfully");
        }

        // User has entered a valid username and password is correct
        else if (currentUserStatus == userStatus.ENTEREDUSERNAME && password.equals(users.get(currentUser)))
        {
            currentUserStatus = userStatus.LOGGEDIN;
            sendMessage("230-Welcome");
            sendMessage("230 User logged in successfully");
        }

        // User is already logged in
        else if (currentUserStatus == userStatus.LOGGEDIN)
        {
            sendMessage("530 User already logged in");
        }

        // Wrong password
        else
        {
            sendMessage("530 Not logged in");
        }
    }


    private void сwd(String args)
    {
        String filename = currentDirectory;

        // go one level up (cd ..)
        if (args.equals(".."))
        {
            int ind = filename.lastIndexOf(fileSeparator);
            if (ind > 0)
            {
                filename = filename.substring(0, ind);
            }
        }

        // if argument is anything else (cd . does nothing)
        else if ((!args.equals(".")) && (args != null))
        {
            filename = filename + fileSeparator + args;
        }

        // check if file exists, is directory and is not above root directory
        File f = new File(filename);

        if (f.exists() && f.isDirectory() && (filename.length() >= root.length()))
        {
            currentDirectory = filename;
            sendMessage("250 The current directory has been changed to " + currentDirectory);
        }
        else
        {
            sendMessage("550 Requested action not taken. File unavailable.");
        }
    }

    private void nlst(String args)
    {
        if (dataConnection == null || dataConnection.isClosed())
        {
            sendMessage("425 No data connection was established");
        }
        else
        {

            String[] dirContent = nlstHelp(args);

            if (dirContent == null)
            {
                sendMessage("550 File does not exist.");
            }
            else
            {
                sendMessage("125 Opening ASCII mode data connection for file list.");

                for (int i = 0; i < dirContent.length; ++i)
                {
                    sendDataMessage(dirContent[i]);
                }

                sendMessage("226 Transfer complete.");
                closeDataConnection();

            }

        }

    }


    private String[] nlstHelp(String args)
    {
        // Construct the name of the directory to list.
        String filename = currentDirectory;
        if (args != null)
        {
            filename = filename + fileSeparator + args;
        }


        // Now get a File object, and see if the name we got exists and is a
        // directory.
        File f = new File(filename);

        if (f.exists() && f.isDirectory())
        {
            return f.list();
        }
        else if (f.exists() && f.isFile())
        {
            String[] allFiles = new String[1];
            allFiles[0] = f.getName();
            return allFiles;
        }
        else
        {
            return null;
        }
    }

    private void port(String args)
    {
        // Split IP address and port number
        String[] stringSplit = args.split(",");
        String hostName = stringSplit[0] + "." + stringSplit[1] + "." +
                stringSplit[2] + "." + stringSplit[3];

        int p = Integer.parseInt(stringSplit[4])*256 + Integer.parseInt(stringSplit[5]);

        // Initiate data connection to client
        openDataConnectionActive(hostName, p);
        sendMessage("200 Command OK");

    }


    private void pwd()
    {
        sendMessage("257 \"" + currentDirectory + "\"");
    }


    private void pasv()
    {

        String ip = "127.0.0.1";
        String splitIp[] = ip.split("\\.");

        int p1 = dataPort/256;
        int p2 = dataPort%256;

        sendMessage("227 Entering Passive Mode ("+ splitIp[0] +"," + splitIp[1] + "," + splitIp[2] + "," + splitIp[3] + "," + p1 + "," + p2 +")");

        openDataConnectionPassive(dataPort);

    }



    /**
     * Handler for the QUIT command.
     */
    private void quit()
    {
        sendMessage("221 Closing connection");
        quitCommandLoop = true;
    }

    private void syst()
    {
        sendMessage("215 COMP1 FTP Server");
    }

    private void mkd(String args)
    {
        // Allow only alphanumeric characters
        if (args != null && args.matches("^[a-zA-Z0-9]+$"))
        {
            File dir = new File(currentDirectory + fileSeparator + args);

            if(!dir.mkdir())
            {
                sendMessage("550 Failed to create new directory");
                debugOutput("Failed to create new directory");
            }
            else
            {
                sendMessage("250 Directory successfully created");
            }
        }
        else
        {
            sendMessage("550 Invalid name");
        }

    }


    private void rmd(String args)
    {
        String filename = currentDirectory;

        // only alphanumeric folder names are allowed
        if (args != null && args.matches("^[a-zA-Z0-9]+$"))
        {
            filename = filename + fileSeparator + args;

            // check if file exists, is directory
            File d = new File(filename);

            if (d.exists() && d.isDirectory())
            {
                d.delete();

                sendMessage("250 Directory was successfully removed");
            }
            else
            {
                sendMessage("550 Requested action not taken. File unavailable.");
            }
        }
        else
        {
            sendMessage("550 Invalid file name.");
        }

    }


    private void type(String mode)
    {
        if(mode.equalsIgnoreCase("A"))
        {
            transferMode = transferType.ASCII;
            sendMessage("200 OK");
        }
        else if(mode.equalsIgnoreCase("I"))
        {
            transferMode = transferType.BINARY;
            sendMessage("200 OK");
        }
        else
            sendMessage("504 Not OK");

    }


    private void retr(String file)
    {
        File f= new File(file);
        if(!f.exists())
        {
            sendMessage("550 File does not exist");
        }

        else
        {

            // Binary mode
            if (transferMode == transferType.BINARY)
            {
                BufferedOutputStream fout = null;
                BufferedInputStream fin = null;

                sendMessage("150 Opening binary mode data connection for requested file " + f.getName());

                try
                {
                    fout = new BufferedOutputStream(dataConnection.getOutputStream());
                    fin = new BufferedInputStream(new FileInputStream(f));
                }
                catch (Exception e)
                {
                    debugOutput("Could not create file streams");
                }

                debugOutput("Starting file transmission of " + f.getName());

                byte[] buf = new byte[1024];
                int l = 0;
                try
                {
                    while ((l = fin.read(buf,0,1024)) != -1)
                    {
                        fout.write(buf,0,l);
                    }
                }
                catch (Exception e)
                {
                    debugOutput("Could not read from or write to file streams");
                    e.printStackTrace();
                }

                //close streams
                try
                {
                    fin.close();
                    fout.close();
                } catch (Exception e)
                {
                    debugOutput("Could not close file streams");
                    e.printStackTrace();
                }


                debugOutput("Completed file transmission of " + f.getName());

                sendMessage("226 File transfer successful. Closing data connection.");

            }

            // ASCII mode
            else
            {
                sendMessage("150 Opening ASCII mode data connection for requested file " + f.getName());

                BufferedReader rin = null;
                PrintWriter rout = null;

                try
                {
                    rin = new BufferedReader(new FileReader(f));
                    rout = new PrintWriter(dataConnection.getOutputStream(),true);

                }
                catch (IOException e)
                {
                    debugOutput("Could not create file streams");
                }

                String s;

                try
                {
                    while((s = rin.readLine()) != null)
                    {
                        rout.println(s);
                    }
                } catch (Exception e)
                {
                    debugOutput("Could not read from or write to file streams");
                    e.printStackTrace();
                }

                try
                {
                    rout.close();
                    rin.close();
                } catch (Exception e)
                {
                    debugOutput("Could not close file streams");
                    e.printStackTrace();
                }
                sendMessage("226 File transfer successful. Closing data connection.");
            }

        }
        closeDataConnection();

    }


    private void stor(String file)
    {
        if (file == null)
        {
            sendMessage("501 No filename given");
        }
        else
        {
                File f = new File(file);
            if(f.exists())
            {
                sendMessage("550 File already exists");
            }

            else
            {

                // Binary mode
                if (transferMode == transferType.BINARY)
                {
                    BufferedOutputStream fout = null;
                    BufferedInputStream fin = null;

                    sendMessage("150 Opening binary mode data connection for requested file " + f.getName());

                    try
                    {
                        fout = new BufferedOutputStream(new FileOutputStream(f));
                        fin = new BufferedInputStream(dataConnection.getInputStream());
                    }
                    catch (Exception e)
                    {
                        debugOutput("Could not create file streams");
                        e.printStackTrace();
                    }

                    debugOutput("Start receiving file " + f.getName());

                    byte[] buf = new byte[1024];
                    int l = 0;
                    try
                    {
                        while ((l = fin.read(buf,0,1024)) != -1)
                        {
                            fout.write(buf,0,l);
                        }
                    }
                    catch (Exception e)
                    {
                        debugOutput("Could not read from or write to file streams");
                        e.printStackTrace();
                    }


                    try
                    {
                        fin.close();
                        fout.close();
                    } catch (IOException e)
                    {
                        debugOutput("Could not close file streams");
                        e.printStackTrace();
                    }


                    debugOutput("Completed receiving file " + f.getName());

                    sendMessage("226 File transfer successful. Closing data connection.");

                }

                // ASCII mode
                else
                {
                    sendMessage("150 Opening ASCII mode data connection for requested file " + f.getName());

                    BufferedReader rin = null;
                    PrintWriter rout = null;

                    try
                    {
                        rin = new BufferedReader(new InputStreamReader(dataConnection.getInputStream()));
                        rout = new PrintWriter(new FileOutputStream(f),true);

                    }
                    catch (IOException e)
                    {
                        debugOutput("Could not create file streams");
                    }

                    String s;

                    try
                    {
                        while((s = rin.readLine()) != null)
                        {
                            rout.println(s);
                        }
                    } catch (Exception e)
                    {
                        debugOutput("Could not read from or write to file streams");
                        e.printStackTrace();
                    }

                    try
                    {
                        rout.close();
                        rin.close();
                    } catch (Exception e)
                    {
                        debugOutput("Could not close file streams");
                        e.printStackTrace();
                    }
                    sendMessage("226 File transfer successful. Closing data connection.");
                }

            }
            closeDataConnection();
        }

    }

    /**
     * Debug output to the console. Also includes the Thread ID for better readability.
     * @param message Debug message
     */
    private void debugOutput(String message)
    {
        if (debugMode)
        {
            System.out.println("Thread " + this.getId() + ": " + message);
        }
    }



}