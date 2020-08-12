#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>

#include "HX711.h"

#define DT_PIN 13
#define CLK_PIN 15


HX711 scale; // DT, CLK
float U;

ESP8266WebServer server(80);

const char *essid="Ледотехника";
const char *key="Eisbrecher";
IPAddress ip(192,168,43,50);  //статический IP
IPAddress gateway(192,168,43,1);
IPAddress subnet(255,255,255,0);


bool is_measuring = false;
float values[1000];
unsigned int times[1000];
int cursor = 0;

void setup() {
  Serial.begin(115200);
  
  scale.begin(DT_PIN, CLK_PIN);
  scale.set_scale();
  Serial.println("Scale ready");

  WiFi.begin(essid,key);
  WiFi.config(ip, gateway, subnet);
  while(WiFi.status() != WL_CONNECTED)
  {
      delay(500);
      Serial.print(".");
  }
  Serial.println("\nWiFi connected");
  
  server.on("/", mainPage);
  server.on("/start/", Start);
  server.on("/stop/", Stop);
  server.on("/get-load/", getLoad);
  server.begin();
  Serial.println("Server started");
}
void loop() {
  server.handleClient();
  if (is_measuring){
    values[cursor] = scale.get_units();
    times[cursor] = millis();
    cursor++;
    if (cursor > 999){
      is_measuring = false;
    }
    delay(20);
  }
}

void mainPage(){
  server.send(200, "text/plain", "Eisbrecher! Datchik volnovogo soprotivlenia");
}

void getLoad(){
  String result = "";
  for (int i=0; i<cursor; i++){
    result += String(times[i]) + ":" + String(values[i]) + "\n";
  }
  cursor = 0;
  server.send(200, "text/plain", result);
}

void Start(){
  is_measuring = true;
  cursor = 0;
  server.send(200, "text/plain", "Measure started");
}

void Stop(){
  is_measuring = false;
  server.send(200, "text/plain", "Measure stoped");
}
