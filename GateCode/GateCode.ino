#include <SoftwareSerial.h>
#define RX 11 // RX(Recieve data) for ESP8266 = TX(Transmit data) OF ARDUINO
#define TX 10 // TX for ESP8266 = RX OF ARDUINO
String AP = "mashton_kitchen";       // AP NAME
String PASS = "hd43v61w"; // AP PASSWORD
String HOST = "192.168.1.145";//IP Address of server
String LocalIP = "Null";
String PORT = "8019";
String URL = "" + HOST + ":" + PORT; //+"/POST.json"
String mode = "1"; //0: Null mode. Wi-Fi RF will be disabled. 1: Station mode. 2: SoftAP mode. 3: SoftAP+Station mode.
int countTrueCommand;
int countTimeCommand;
boolean found = false;
String valSensor = "";
SoftwareSerial esp8266(TX, RX); //(From ESP8266(3.3V) to Arduino, From Arduino(5V!) to ESP8266(3.3V!))

// defines pins numbers
const int trigPin = 5;
const int echoPin = 6;
// defines variables
long duration;
int distance;
long durationstart;
int distanceMax = 0;
String p = "Gate 2";

void setup() {
  Serial.begin(9600);
  esp8266.begin(115200);//115200
  sendCommand("AT", 5, "OK");
  sendCommand("AT+CWMODE=" + mode, 5, "OK");
  sendCommand("AT+CIPMUX=1", 5, "+CIPMUX:1");
  sendCommand("AT+CWQAP", 15, "OK");
  sendCommand("AT+CWJAP=\"" + AP + "\",\"" + PASS + "\"", 15, "OK");
  openConnection();

  pinMode(trigPin, OUTPUT); // Sets the trigPin as an Output
  pinMode(echoPin, INPUT); // Sets the echoPin as an Input
  durationstart = pulseIn(echoPin, HIGH);
  // Calculating the distance
  distanceMax = durationstart * 0.034 / 2;
}//send the message to the server

void loop() {
  // Clears the trigPin
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  // Sets the trigPin on HIGH state for 10 micro seconds
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);
  // Reads the echoPin, returns the sound wave travel time in microseconds
  duration = pulseIn(echoPin, HIGH);
  // Calculating the distance
  distance = duration * 0.034 / 2;
  // Prints the distance on the Serial Monitor
  //Serial.print("Max distance:");
  //Serial.print(distanceMax);
  Serial.print("Distance: ");
  Serial.println(distance);

  if (distance <  distanceMax * .75) {
    valSensor = "Gate 1";
    HTTPsend();
    Serial.println("Person detected");
    delay(1000);
    Serial.println("Recommencing monitoring");
  }

}

void HTTPsend() {

  p = "Gate" + String(floor(random(0,3)), 0);
  notifyMessageSize();
  sendMessage();
  countTrueCommand++;
}

bool ping() {
  Serial.println("About to ping");
  return sendCommand("AT+PING=\"" + HOST + "\"", 20, "OK");
}

void reconnectAP() {
  Serial.println("About to reset AP connection");
  sendCommand("AT+CWQAP", 20, "OK"); // Reset Access Point connection
  Serial.println("About to reconnect AP");
  sendCommand("AT+CWJAP=\"" + AP + "\",\"" + PASS + "\"", 20, "OK"); //Reconnect to access point
  Serial.println("Finished reconnecting to AP");
}

void openConnection() {
  Serial.println("About to start a TCP/IP connection");
  sendCommand("AT+CIPSTART=0,\"TCP\",\"" + HOST + "\"," + PORT, 15, "OK"); //Start a TCP/IP connection with the RPi Python code
}
void notifyMessageSize() {
  Serial.println("About to tell the server the length of the message");
  sendCommand("AT+CIPSEND=0," + String(p.length()), 0, "OK"); // Tell the server the length of the message
}
void sendMessage() {

  Serial.println("About to send the message");
  sendCommand(p, 0, "SEND OK"); // Send the message
}

void closeConnection() {
  Serial.println("About to close the connection.");
  sendCommand("AT+CIPCLOSE=0", 15, "OK"); // Close the connection
  Serial.println("Closed the connection");
}

int getSensorData() {
  return random(1000); // Replace with your own sensor code
}



bool sendCommand(String command, int maxTime, char readReplay[]) {
  Serial.print(countTrueCommand);
  Serial.print(". at command => ");
  Serial.print(command);
  Serial.println(" ");
  esp8266.println(command);//at+cipsend
  while (countTimeCommand < (maxTime * 1))
  {
    //Serial.println("ESP8266 return: "+ (String)esp8266.read()); //28/03/2022 10:11
    //esp8266.println(command);//at+cipsend
    //Serial.print(esp8266.read());
    if (esp8266.find(readReplay)) //ok
    {
      found = true;
      //return true;
      break;
    }

    countTimeCommand++;
  }

  if (found == true)
  {
    Serial.println("Good");
    countTrueCommand++;
    countTimeCommand = 0;
    return true;
  }

  if (found == false)
  {
    Serial.println("Fail");
    countTrueCommand = 0;
    countTimeCommand = 0;
    return false;
  }

  found = false;
  return false;
}
