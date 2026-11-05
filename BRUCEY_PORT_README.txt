ESP-HACK -> Brucey ESP32-S3 first-pass port

Board:
ESP32-S3 N16R8
SSD1306 128x64 I2C 0x3C

Pins:
OLED SDA17 SCL18
Buttons UP1 DOWN4 BACK5 RIGHT6 OK7
SPI SCK12 MISO13 MOSI11
CC1101 CS10 GDO0 2
NRF24 CSN14 CE15
microSD CS46
IR TX9 RX8

Build environment:
BRUCEY_S3_SSD1306

IMPORTANT:
- This is a first-pass hardware port, not yet hardware-verified.
- SD, CC1101 and NRF24 physically share the same SPI wires on this PCB.
- The upstream project was designed around different wiring, so shared-SPI
  conflicts may still need a second patch after the first build/runtime test.
- Active interference/jamming entry was removed from the NRF24 menu in this port.

V2 BUILD FIX
- ESP32-S3 lwIP defines MEM_SIZE=1600 globally.
- Bundled OneWireHub also uses MEM_SIZE as class constants.
- Added a local #undef MEM_SIZE in OneWireHub/src/platform.h after Arduino.h.
- This resolves DS2408/DS2423/DS2431/DS2433/DS2438/DS2450/DS2502/DS2506 build errors.

V3 BUILD FIX
- The next blocker was src/ble_spam.h including legacy esp_gap_ble_api.h.
- BLE advertising-spam has been removed from this ESP32-S3 port.
- bluetooth.cpp now uses only the existing NimBLE HID paths.
- Bluetooth menu now contains BadBLE and Mouse only.
- ble_spam.cpp is excluded from PlatformIO compilation.
- OneWireHub MEM_SIZE fix from V2 is preserved.

V4 SHARED SPI FIX
- Runtime SD failure showed the first port still used a second SPIClass for SD.
- This PCB physically shares SCK12/MISO13/MOSI11 between SD, CC1101 and NRF24.
- V4 uses Arduino's ONE global SPI object for all three.
- Before SD: CC CS10 HIGH, NRF CSN14 HIGH, CE15 LOW.
- SD retries at 400k, 1MHz and 4MHz.
- Before NRF24: SD is ended/deselected and CC CS is held HIGH.
- Before CC1101: SD is ended/deselected and NRF CSN is held HIGH.

V5 LINK FIX
- V4 correctly removed the dedicated sdSPI object, but gpio.cpp and wifi.cpp
  still referenced it.
- Removed all remaining 'extern SPIClass sdSPI' declarations.
- Replaced all sdSPI.end()/begin()/SD.begin(...sdSPI...) calls with the one
  shared global SPI object on SCK12/MISO13/MOSI11.
- This fixes the linker errors from saveIButtonToSD() and stopEvilPortal().

V6 RF STABILITY PATCH
- Standalone V7 diagnostic proved BOTH FSPI and HSPI work on SCK12/MISO13/MOSI11.
- CC1101 direct result: PART=00 VER=14.
- NRF24 direct result: STATUS=0E AW=03.
- Therefore the previous RF failures were caused by shared-bus state, not bad pins/modules.
- SD boot initialization is skipped because the SD interface still gives invalid raw SPI responses.
- NRF24 now explicitly ends/restarts SPI and performs a 125 kHz register probe before RF24 init.
- CC1101 now explicitly ends/restarts SPI and performs a 125 kHz VERSION probe before library init.

V7 BOOT FIX
- Root cause of "OLED only works when Serial Monitor is open" found.
- setup() contained: while (!Serial) delay(10);
- On ESP32-S3 native USB CDC this blocks the entire firmware until a host opens the serial port.
- Removed the blocking wait. Device now boots normally from battery or USB with no Serial Monitor.

V8 SD MISO SPLIT
- Move SD MISO physically from GPIO13 to GPIO3.
- RF: SCK12 / MOSI11 / MISO13.
- SD: SCK12 / MOSI11 / MISO3 / CS46.
- SD boot init re-enabled.
- RF SPI routing restored to MISO13 after SD init.

V9 FINALIZED SD GPIO3 WIRING
- Battery-only OLED raw-SD test confirmed:
  CMD0=01, CMD8=01, R7=00 00 01 AA.
- Proven SD wiring:
  CS46, SCK12, MOSI11, MISO3.
- RF remains:
  SCK12, MOSI11, MISO13.
- SD init now tries 100k, 400k, 1MHz, then 4MHz.
- After SD init, SPI routing is restored to RF MISO13.
- Serial Monitor is NOT required for boot.

V10 FIXES
- The raw battery SD diagnostic proved GPIO3 SD wiring works:
  CMD0=01, CMD8=01, R7=00 00 01 AA.
- V9 still mounted SD through the same global SPI object used for RF.
- V10 gives SD a dedicated HSPI object:
  SD: SCK12 MOSI11 MISO3 CS46.
- RF remains on global SPI:
  SCK12 MOSI11 MISO13.
- All SD.begin() paths in main/gpio/wifi now use sdSPI.
- CC1101 upstream library connection check was rejecting a module that the
  direct probe consistently reads as VER=14.
- V10 verifies CC1101 with the known-good direct transaction before and after Init().

V11 BUILD FIX
- wifi.cpp referenced the dedicated sdSPI object but did not declare it.
- Added: extern SPIClass sdSPI;
- No runtime logic changed from V10.

V12 FULL-FILES BUILD
- Based on V11 hardware/SD/RF fixes.
- NO upstream repository files are discarded.
- Every original ESP-HACK file is preserved untouched under /upstream_original/.
- Original src/ble_spam.cpp and src/ble_spam.h are restored in /src as well.
- ble_spam.cpp remains excluded from compilation because upstream depends on
  legacy esp_gap_ble_api.h / Bluedroid APIs that do not compile in this S3 build.
- NRF24 Spectrum + Config remain available with Brucey pins.
- SD remains MISO3 and dedicated sdSPI; RF remains MISO13.

V13 ALL-FILES / FULL-MENU
- No source file is excluded from compilation.
- Restored original Bluetooth menu: Spam / BadBLE / Mouse.
- Restored original bluetooth.cpp controller flow.
- src/ble_spam.cpp and src/ble_spam.h are present and compiled with an ESP32-S3
  compatibility implementation. Exact untouched upstream versions remain under
  upstream_original/src/.
- Restored NRF24 menu layout: Jammer / Spectrum / Config.
- Spectrum and Config use the Brucey NRF24 pins.
- The Jammer entry remains visible but does not emit a disruptive carrier.
- V11/V12 hardware pin, OLED, SD GPIO3, CC1101 and boot fixes are retained.

V14 FULL MENU / NO FILE DELETION
- No upstream source files are deleted.
- No source files are excluded from compilation.
- Original Bluetooth menu remains: Spam / BadBLE / Mouse.
- Original NRF24 menu remains: Jammer / Spectrum / Config.
- Original NRF24 mode names are restored in the menu.
- Original Wi-Fi menu names remain present.
- Hardware fixes from V11+ remain:
  OLED SDA17/SCL18, SD MISO3 CS46, RF MISO13, CC CS10, NRF CSN14/CE15.
- Exact upstream copies remain under /upstream_original/.
- Disruptive RF/BLE/Wi-Fi transmission routines are not activated in this port;
  the files and menu structure are preserved so unrelated tools stay intact.

V15 NRF24 MENU FIX
- No upstream source files are deleted or excluded.
- The old first NRF24 menu entry no longer dead-ends with "Unavailable".
- It now launches a live receive-only RF24 channel activity monitor using the
  same proven radio initialization as Spectrum.
- Spectrum and Config remain unchanged.
- Exact original upstream files remain preserved under /upstream_original/.

V16 NRF24 MENU SEPARATION
- No files deleted or excluded.
- NRF24 menu now has four separate entries:
  Jammer / RF Monitor / Spectrum / Config.
- The Jammer entry no longer replaces or blocks RF Monitor.
- RF Monitor, Spectrum and Config remain independently selectable.
- Original upstream jammer files and mode names remain preserved.

V17 PN532 + NRF24 HARDWARE MENU
- No upstream source files removed.
- GPIO menu now shows:
  iButton / NRF24 / PN532 NFC / ST25R3916
- PN532 matches Brucey hardware:
  I2C SDA17, SCL18, address 0x24, module switch 1 ON / 2 OFF.
- PN532 tools added:
  Scan Tag (ISO14443A UID read-only)
  Module Info (chip/firmware/I2C info)
- NRF24 menu remains:
  Jammer / RF Monitor / Spectrum / Config
  RF Monitor, Spectrum and Config use CE15/CSN14/SCK12/MOSI11/MISO13.
- SD remains on MISO3/CS46 with dedicated sdSPI.
- ST25R3916 original menu remains preserved even though Brucey has PN532 hardware.

V18 BLE ADVERTISING FIX
- V17 BLE Spam compatibility code only printed to Serial and did not transmit.
- V18 now uses NimBLE on ESP32-S3 to perform a real, normal BLE advertisement.
- Device advertises as: Brucey BLE Test
- Advertising interval: 100-200 ms.
- This verifies the S3 BLE radio and BLE menu path without an advertising flood.
- Original untouched upstream BLE-spam source remains under upstream_original/.

V19 MORE HARDWARE TOOLS
- BadBLE now auto-creates three benign .txt demo scripts on SD:
  /badkb/hello.txt
  /badkb/typing_test.txt
  /badkb/delay_test.txt
- NRF24 menu expanded:
  Jammer / RF Monitor / Spectrum / Channel Meter / Radio Info / Config
- Channel Meter is receive-only and shows activity per channel.
- Radio Info shows chip connection/channel/address width/CRC/PA info.
- PN532 menu expanded:
  Scan UID / UID Logger / Module Info
- UID Logger writes scans to /nfc/uids.txt on the SD card.
- Games expanded:
  Snake / Bird / Bricks / Pong / Doom / Reaction / Dice
- No upstream files removed.

V20 NFC BUSINESS-CARD TOOLS
- PN532 menu:
  Scan UID
  Read NDEF
  Copy NDEF
  Write Copy
  Write URL
  Write Text
  UID Logger
  Module Info
- Copy/Write Copy duplicates the NDEF business-card CONTENT, not the tag UID.
- Write URL reads /nfc/business_url.txt
- Write Text reads /nfc/business_text.txt
- Template files are auto-created on SD so they can be edited easily.
- Designed for writable NTAG / MIFARE Ultralight-style Type-2 NFC tags.
- No upstream project files removed.

V21 BUILD FIX
- Fixed RF24 compatibility error in drawNRF24RadioInfo().
- This RF24 library exposes setAddressWidth() but not getAddressWidth().
- Removed the unsupported getter; no hardware logic or menu tools were removed.
- Keeps all V20 NFC business-card tools, BadBLE sample files, NRF24 tools and games.

V22 NFC ERASE + IR 3X
- PN532 menu adds "Erase NDEF".
- Erase NDEF writes an empty Type-2 NDEF TLV to page 4.
  It does NOT alter UID, OTP bytes, lock bytes, or passwords.
- Saved IR "Send" now transmits the selected signal 3 times.
- TV-B-Gone now transmits each power code 3 times with a short gap.
- 3x repetition improves reception probability; it does not increase IR LED power.
- All V21 tools and source files are retained.

V23 FINAL CANDIDATE
IR:
- "Send" restored to normal single-send behavior.
- Added separate "Send 3x".
- TV-B-Gone remains 3x per power code.
- Remote / Read remain present.

SubGHz:
- Analyzer now remembers the last detected/locked frequency.
- Leaving Analyzer automatically retunes Read / Read RAW to that frequency.
- This fixes a common case where Analyzer sees a remote but Read is listening
  on a different frequency.
- Unsupported/rolling/encrypted protocols may still only appear as RAW activity.

NFC:
- Added "Tag Info".
- NDEF copy/write/erase remains for writable NFC business-card style tags.
- Erase NDEF clears user NDEF data only; UID/lock/OTP/security areas are untouched.
- PN532 cannot make every NFC technology writable; locked/protected/unsupported
  cards will remain read-only or unsupported.

No upstream files were deleted.

V24 FINAL IR SPLIT
- Send = normal 1x.
- Send 3x = three repeats.
- TV-B-Gone = each TV power code sent once.
- TV-B-Gone 3x = each TV power code sent three times.
- Read and Remote remain separate.
- All V23 SubGHz, NFC, NRF24, SD, BLE and game changes are retained.
