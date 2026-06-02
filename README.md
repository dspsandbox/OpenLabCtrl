# OpenLabCtrl
Library for Synchronous and Deterministic Control of Red Pitaya's Digital and Analog IOs.

## Features:
* Real-time control (8ns resolution) of:
  * RF out (x2): amplitude, frequency, phase
  * RF in (x2): acquisition, decimation
  * Digital IOs (x16): direction, output value, input acquisition
  * Serial communication: SPI, UART (via Digital IOs)
  * LEDs (x8): output value
  * Analog out, PWM + LPF (x4): output value 
  * Analog in, XADC (x4): acquisition, decimation

* Experimental sequences with:
   * Independent and parametrizable sub-sequences (*IoSyncFrames*, *ParemetrizedIoSyncFrames*) for modular coding and reduced compilation time
   * External triggering
   * Multi-device synchronization 

* Buffer size:
    * Instructions: 16MB, 2M instructions
    * Scope/Acquisition (x2): 8MB, 4M samples

## Supported Devices
* Redpitaya-125-14-z7010:
    * STEMlab 125-14 (Gen 1) 
    * STEMlab 125-14 Low Noise (Gen 1)
    * STEMlab 125-14 (Gen 2)
    * STEMlab 125-14 Pro (Gen 2)
* Redpitaya-125-14-z7020:
    * STEMlab 125-14 Z7020 Low Noise (Gen 1)
    * STEMlab 125-14 Pro Z7020 (Gen 2)
## Installation
### Dependencies
Please install the Zynq TCP Control library (TCP-based control utilities for ZYNQ FPGA boards, enabling remote bitstream loading and memory IO). 
* Clone the repository
    ``` 
    git clone https://github.com/dspsandbox/zynq_utils/tree/master/zynq_tcp_ctrl
    ```
  
* Follow the remote & local [installation instructions](https://github.com/dspsandbox/zynq_utils/blob/master/zynq_tcp_ctrl/README.md)

### This Library
* Clone the Zynq TCP Control repository:
  ```
  git clone https://github.com/dspsandbox/openlabctrl/tree/main
  ```

* Navigate to the python lib and install via pip3 (-e for editable install):
    ```
    cd openlabctrl
    python3 -m pip install --upgrade pip setuptools wheel
    pip3 install -e .
    ```

## Documentation
See [Pyhton API Reference](https://dspsandbox.github.io/openlabctrl/) (latest version).

## Examples
|Notebook | Description|
|-|-|
[00_led_blink.ipynb](example/00_led_blink.ipynb) | Turn on/off LEDs with external triggering.          
[01_digital_in_out.ipynb](example/01_digital_in_out.ipynb) | Configure digital IO direction and square wave generation
[02_serial.ipynb](example/02_serial.ipynb) | Examples of UART and SPI transaction via digital IOs
[03_analog_in_out.ipynb](example/03_analog_in_out.ipynb) | Generation and acquisition of analog ramps via slow analog IOs 
[04_rf_in_out.ipynb](example/04_rf_in_out.ipynb) | RF synthesis and acquisition via high-speed analog IOs
[05_param_io_frame.ipynb](example/05_param_io_frame.ipynb) | Parametrizable IO frames and configurable sequences 
[06_multi_device_sync.ipynb](example/06_multi_device_sync.ipynb) | Multi-device synchronization and scalability 


## IOs & Pin Mapping

![](https://redpitaya.readthedocs.io/en/latest/_images/Red_Pitaya_pinout.jpg)


|IO Name (OpenLabCtrl library) | Pin Name (see diagram above) | Description|
|-|-|-|
led[0-7] | LED_0-7 | User LEDs
digital_io_0[0] | DIO0_P (trig ext) | Digital IO (3.3V) 
digital_io_0[1] | DIO0_N  | Digital IO (3.3V)
digital_io_0[2] | DIO1_P | Digital IO (3.3V)  
digital_io_0[3] | DIO1_N  | Digital IO (3.3V) 
digital_io_1[0] | DIO2_P  | Digital IO (3.3V) 
digital_io_1[1] | DIO2_N  | Digital IO (3.3V) 
digital_io_1[2] | DIO3_P  | Digital IO (3.3V) 
digital_io_1[3] | DIO3_N  | Digital IO (3.3V) 
digital_io_2[0] | DIO4_P  | Digital IO (3.3V) 
digital_io_2[1] | DIO4_N  | Digital IO (3.3V) 
digital_io_2[2] | DIO5_P  | Digital IO (3.3V) 
digital_io_2[3] | DIO5_N  | Digital IO (3.3V) 
digital_io_3[0] | DIO6_P  | Digital IO (3.3V) 
digital_io_3[1] | DIO6_N  | Digital IO (3.3V) 
digital_io_3[2] | DIO7_P  | Digital IO (3.3V) 
digital_io_3[3] | DIO7_N  | Digital IO (3.3V) 
analog_in_0 | Analog input 0 | Slow analog input (0V-3.5V, 12-bit, 250 KSa/s)
analog_in_1 | Analog input 1 | Slow analog input (0V-3.5V, 12-bit, 250 KSa/s)
analog_in_2 | Analog input 2 | Slow analog input (0V-3.5V, 12-bit, 250 KSa/s)
analog_in_3 | Analog input 3 | Slow analog input (0V-3.5V, 12-bit, 250 KSa/s)
analog_out_0 | Analog Output 0 | Slow analog output (0V-1.8V, 12-bit, fc = 190kHz)
analog_out_1 | Analog Output 1 | Slow analog output (0V-1.8V, 12-bit, fc = 190kHz)
analog_out_2 | Analog Output 2 | Slow analog output (0V-1.8V, 12-bit, fc = 190kHz)
analog_out_3 | Analog Output 3 | Slow analog output (0V-1.8V, 12-bit, fc = 190kHz)
rf_out_0 | OUT1 | Fast analog output (+/-1V, 14-bit, 125 MSa/s)
rf_out_2 | OUT2 | Fast analog output (+/-1V, 14-bit, 125 MSa/s)
rf_in_0 | IN1 | Fast analog input (+/-1V or +/-20V, 14-bit, 125 MSa/s)
rf_in_1 | IN2 | Fast analog input (+/-1V or +/-20V, 14-bit, 125 MSa/s)
daisy_0 | S1 | Synchronization connector (gen 1: SATA, gen 2: USB-C)
daisy_1 | S2 | Synchronization connector (gen 1: SATA, gen 2: USB-C)













