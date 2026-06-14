/*
  SENSOR DE COLOR PARA EL ROBOT NIRYO (VERSION 3)
  ================================================
  En esta version el Arduino ya NO decide el color.
  Ahora es mas sencillo: solo MIDE y envia los numeros.

  El ordenador (Python) es quien aprende los colores y decide,
  comparando con los cubos que le ensenaste al principio.

  Funcionamiento:
  - El ordenador envia la letra 'C' por el USB.
  - El Arduino responde 4 numeros separados por comas:
        rojo,verde,azul,luz
    Por ejemplo:  523,310,295,1450

  CONEXIONES DEL SENSOR KEYESTUDIO TCS34725 AL ARDUINO UNO:
  ---------------------------------------------------------
     Sensor VCC (o V)  --->  Arduino 5V
     Sensor GND (o G)  --->  Arduino GND
     Sensor SDA        --->  Arduino A4
     Sensor SCL        --->  Arduino A5

  Recuerda instalar la libreria "Adafruit TCS34725" en el Arduino IDE.
*/

#include <Wire.h>
#include "Adafruit_TCS34725.h"

// Lectura rapida (50 ms) y ganancia 4x
Adafruit_TCS34725 sensor = Adafruit_TCS34725(TCS34725_INTEGRATIONTIME_50MS,
                                             TCS34725_GAIN_4X);

void setup() {
  Serial.begin(9600);

  if (sensor.begin()) {
    Serial.println("LISTO");
  } else {
    Serial.println("ERROR");   // Revisa los cables del sensor
  }
}

void loop() {
  if (Serial.available() > 0) {
    char letra = Serial.read();

    if (letra == 'C') {
      // Leemos el sensor: r = rojo, g = verde, b = azul, c = luz total
      uint16_t r, g, b, c;
      sensor.getRawData(&r, &g, &b, &c);

      // Enviamos los 4 numeros separados por comas
      Serial.print(r);
      Serial.print(",");
      Serial.print(g);
      Serial.print(",");
      Serial.print(b);
      Serial.print(",");
      Serial.println(c);
    }
  }
}
