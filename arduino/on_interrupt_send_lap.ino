/**
 * An Arduino program for signaling PC when a lap sensor is triggered.
 * 
 * It uses interrupts to detect a change in pins D4, D5, D6 or D7 and 
 * sends the signal via serial (115200 8N1) as "1", "2", "3" or "4".
 * 
 * There is a 1000 ms cooldown after a trigger to avoid issues with sensor
 * voltage bounce (the laps cannot be shorter than 1 s).
 * 
 * The PIN CHANGE interrupt handler ISR is minimalistic and the handling of 
 * state is done in the loop(). The communication between interrupt handler 
 * and the  loop is done through volatile pin_triggered bool array.
 * 
 * @author Jussi Rasku
 * @copyright Copyright (C) 2022 Jussi Rasku
 * @license MIT 
 * @version 1.0
 */

#define MIN_LAP_TIME_MS 1000

volatile bool pin_triggered[4] = {false,false,false,false};
bool sent_triggered[4] = {false,false,false,false};
long last_triggered[4] = {0,0,0,0};


void setup() {
  Serial.begin(115200);

  pinMode(LED_BUILTIN, OUTPUT);
  
  pinMode(4, INPUT_PULLUP);
  pinMode(5, INPUT_PULLUP);
  pinMode(6, INPUT_PULLUP);
  pinMode(7, INPUT_PULLUP);

  // Setup PIN CHANGE interrupts
  //   Enable PCIE2 Bit3 = 1 (Port D)
  PCICR |= B00000100;
  //   Select PCINT23 Bit4-7 = 1 (Pin D4,D5,D6,D7)
  PCMSK2 |= B11110000;
}

void loop() {
  // loop resets the triggers to avoid bounce
  
  long tick = millis();
  bool all_waiting = true;
  for (int i=0 ; i<4 ; i++) {
    if (pin_triggered[i]) {
      all_waiting = false;
      if (!sent_triggered[i]) {
        Serial.print(i+1);
        sent_triggered[i] = true;
        last_triggered[i] = tick;
        digitalWrite(LED_BUILTIN, HIGH);
      } else if (tick-last_triggered[i]>MIN_LAP_TIME_MS) {
        pin_triggered[i] = false;
        sent_triggered[i] = false;
      }
    }
  }
  if (all_waiting) digitalWrite(LED_BUILTIN, LOW);
}

ISR (PCINT2_vect)
{
  for (int i=0 ; i<4 ; i++) {
    if (!pin_triggered[i] && digitalRead(4+i)==LOW) pin_triggered[i] = true;
  }
}
