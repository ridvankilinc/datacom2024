#define _WIN32_WINNT 0x0600
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <winsock2.h>
#include <ws2tcpip.h>

#pragma comment(lib, "Ws2_32.lib")

#define PORT 8080
#define BUFFER_SIZE 1024
#define SERVER_IP "127.0.0.1"

void clear_socket_buffer(SOCKET sock) {
    char temp_buffer[BUFFER_SIZE];
    unsigned long ul = 1;
    ioctlsocket(sock, FIONBIO, &ul);

    int bytes_received;
    do {
        bytes_received = recv(sock, temp_buffer, BUFFER_SIZE - 1, 0);
    } while (bytes_received > 0);

    ul = 0;
    ioctlsocket(sock, FIONBIO, &ul);
}

void run_client() {
    WSADATA wsaData;
    SOCKET sock;
    struct sockaddr_in serv_addr;
    char buffer[BUFFER_SIZE] = {0};
    char input_buffer[BUFFER_SIZE] = {0};

    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
        printf("WSAStartup failed\n");
        return;
    }

    if ((sock = socket(AF_INET, SOCK_STREAM, 0)) == INVALID_SOCKET) {
        printf("Socket creation failed\n");
        WSACleanup();
        return;
    }

    serv_addr.sin_family = AF_INET;
    serv_addr.sin_port = htons(PORT);
    serv_addr.sin_addr.s_addr = inet_addr(SERVER_IP);

    if (serv_addr.sin_addr.s_addr == INADDR_NONE) {
        printf("Invalid address\n");
        closesocket(sock);
        WSACleanup();
        return;
    }

    if (connect(sock, (struct sockaddr*)&serv_addr, sizeof(serv_addr)) == SOCKET_ERROR) {
        printf("Connection Failed\n");
        closesocket(sock);
        WSACleanup();
        return;
    }

    int bytes_received = recv(sock, buffer, BUFFER_SIZE - 1, 0);
    if (bytes_received > 0) {
        buffer[bytes_received] = '\0';
        printf("%s", buffer);
    } else {
        printf("Error receiving initial message\n");
        closesocket(sock);
        WSACleanup();
        return;
    }

    bytes_received = recv(sock, buffer, BUFFER_SIZE - 1, 0);
    if (bytes_received > 0) {
        buffer[bytes_received] = '\0';
        printf("%s", buffer);
    }

    while (1) {
        printf("\nChoose an action:\n");
        printf("1. List Products\n");
        printf("2. View Cart\n");
        printf("3. Checkout\n");
        printf("4. Exit\n");
        printf("Choose an option: ");

        fgets(input_buffer, BUFFER_SIZE, stdin);
        int choice = atoi(input_buffer);

        memset(buffer, 0, BUFFER_SIZE);
        memset(input_buffer, 0, BUFFER_SIZE);

        switch (choice) {
            case 1:
                strcpy(buffer, "1");
                break;
            case 2:
                strcpy(buffer, "2");
                break;
            case 3:
                strcpy(buffer, "3");
                break;
            case 4:
                strcpy(buffer, "4");
                send(sock, buffer, strlen(buffer), 0);
                closesocket(sock);
                WSACleanup();
                return;
            default:
                printf("Invalid choice. Try again.\n");
                continue;
        }

        clear_socket_buffer(sock);

        if (send(sock, buffer, strlen(buffer), 0) == SOCKET_ERROR) {
            printf("Send failed\n");
            break;
        }

        if (choice == 1) {
            int menu_level = 1;
            while (1) {
                switch (menu_level) {
                    case 1:
                        bytes_received = recv(sock, buffer, BUFFER_SIZE - 1, 0);
                        if (bytes_received > 0) {
                            buffer[bytes_received] = '\0';
                            printf("%s", buffer);
                            
                            printf("Enter category number (0 to go back): ");
                            fgets(input_buffer, BUFFER_SIZE, stdin);
                            input_buffer[strcspn(input_buffer, "\n")] = 0;
                            
                            if (input_buffer[0] == '0') {
                                send(sock, "0", 1, 0);
                                menu_level = 0;
                                break;
                            }
                            
                            send(sock, input_buffer, strlen(input_buffer), 0);
                            menu_level = 2;
                        }
                        break;
                    
                    case 2:
                        bytes_received = recv(sock, buffer, BUFFER_SIZE - 1, 0);
                        if (bytes_received > 0) {
                            buffer[bytes_received] = '\0';
                            printf("%s", buffer);
                            
                            printf("Enter product number (0 to go back to categories): ");
                            fgets(input_buffer, BUFFER_SIZE, stdin);
                            input_buffer[strcspn(input_buffer, "\n")] = 0;
                            
                            if (input_buffer[0] == '0') {
                                send(sock, "0", 1, 0);
                                menu_level = 1; 
                                break;
                            }
                            
                            send(sock, input_buffer, strlen(input_buffer), 0);
                            
                            bytes_received = recv(sock, buffer, BUFFER_SIZE - 1, 0);
                            if (bytes_received > 0) {
                                buffer[bytes_received] = '\0';
                                printf("%s", buffer);
                            }
                        }
                        break;
                }
                
                if (menu_level == 0) {
                    break;
                }
            }
        }
        else {
            bytes_received = recv(sock, buffer, BUFFER_SIZE - 1, 0);
            if (bytes_received > 0) {
                buffer[bytes_received] = '\0';
                printf("%s", buffer);
            }
        }
    }

    closesocket(sock);
    WSACleanup();
}

int main() {
    run_client();
    return 0;
}