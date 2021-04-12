package com.company;
import java.io.IOException;
import java.net.ServerSocket;
import java.net.Socket;

public class Server
{
    private int controlPort = 1025;
    private ServerSocket serverSocket;
    boolean serverRunning = true;

    public static void main(String[] args)
    {
        new Server();
    }

    public Server()
    {
        try
        {
            serverSocket = new ServerSocket(controlPort);
        }
        catch (IOException e)
        {
            System.out.println("Could not create server socket");
            System.exit(-1);
        }

        System.out.println("FTP Server started listening on port " + controlPort);

        int threadsNumber = 0;

        while (serverRunning)
        {

            try
            {
                Socket client = serverSocket.accept();

                // Port for incoming dataConnection
                int dataPort = controlPort + threadsNumber + 1;

                // Create new thread for new connection
                ClientWork w = new ClientWork(client, dataPort);

                System.out.println("New connection received. Worker was created.");
                threadsNumber++;
                w.start();
            }
            catch (IOException e)
            {
                System.out.println("Exception encountered on accept");
                e.printStackTrace();
            }

        }
        try
        {
            serverSocket.close();
            System.out.println("Server was stopped");

        } catch (IOException e)
        {
            System.out.println("Problem stopping server");
            System.exit(-1);
        }

    }



}
