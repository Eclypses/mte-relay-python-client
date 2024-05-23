

<img src="Eclypses.png" style="width:50%;margin-right:0;"/>

<div align="center" style="font-size:40pt; font-weight:900; font-family:arial; margin-top:300px; " >
MTE Relay Client Demo (Python)</div>
<br>
<div align="center" style="font-size:28pt; font-family:arial; " >
Demo for MTE Relay</div>
<br>
<div align="center" style="font-size:15pt; font-family:arial; " >
Using MTE version 4.x.x</div>

[Introduction](#introduction)

[Language Interface Unit Test](#language-test)


<div style="page-break-after: always; break-after: page;"></div>

# Introduction

This project utilizes locust to simulate multiple users making many requests against the MTE relay server.

**IMPORTANT**
>Please note the solution provided in this tutorial does NOT include the MTE library or supporting MTE library files. Please contact Eclypses Inc. if the MTE SDK (which contatins the library and supporting files) has NOT been provided. The solution will only work AFTER the MTE library and other files have been incorporated.

# MTE Relay Client Demo

## Setup
Ensure that the python module "locust" is installed.

## MTE Directory and File Setup
<ol>
<li>
Copy the "lib" directory and contents from the MTE SDK into the root directory.
</li>
<li>
Copy the "src/py" directory and contents from the MTE SDK into the root directory.
</li>
<li>
In the file locustRequest.py, locate the line in the source code 
```Python
 if not MteBase.init_license("LicenseCompany", "LicenseKey"):
```
and replace "LicenseCompany" and "LicenseKey" with the appropriate company and license key provided by the Eclypses Applied Technology Team <a href="https://eclypses.com/get-started/">https://eclypses.com/get-started/</a>
</li>
</ol>

<div style="page-break-after: always; break-after: page;"></div>

## Usage
1. Open a command line interface:
    * Windows: Open Command Prompt or PowerShell
    * Linux: Open Terminal
    * macOS: Open Terminal
2. Navigate to the project directory:

```bash
cd path/to/project
```

3. Run Locust:
```bash
locust -f locustRequest.py --headless -u 100 -r10 -t 10m --csv a.csv --host https://aws-relay-server.eclypses.com/ --test_type login --mte_type 1 --total_pairs 10
```

### Program Arguments

There are several program arguments that can be used to control the client test. They can be used either in the terminal or in a "launch.json" file. There are many that locust itself offers; this covers the main ones this application utilizes, along with several custom arguments. These custom arguments are specific to MTE testing capabilities.

<ul>
<li>
-f: The name of the python file that locust will use. In this application, it should always be locustRequest.py. Other python files will be incorporated as needed.
</li>
<li>
--headless: Disables the web interface.
</li>
<li>
-u: The peak number of concurrent users.
</li>
<li>
-r: The rate at which users are spawn.
</li>
<li>
-t: The total run time. For example, "10m" will run for 10 minutes. 
</li>
<li>
--csv: Stores statistics to CSV format files.
</li>
<li>
--host: Host to load test against.
</li>
<li>
--test_type: The particular test to run. *Custom argument*
</li>
<li>
--mte_type: 1 or "mke" to use the MKE add-on, otherwise it will use the core MTE. *Custom argument*
</li>
<li>
--total_pairs: The total number of encoder/decoder states that will match up with the server. *Custom argument*
</li>
</ul>


# Contact Eclypses

<img src="Eclypses.png" style="width:8in;"/>

<p align="center" style="font-weight: bold; font-size: 20pt;">Email: <a href="mailto:info@eclypses.com">info@eclypses.com</a></p>
<p align="center" style="font-weight: bold; font-size: 20pt;">Web: <a href="https://www.eclypses.com">www.eclypses.com</a></p>
<p align="center" style="font-weight: bold; font-size: 20pt;">Chat with us: <a href="https://developers.eclypses.com/dashboard">Developer Portal</a></p>

<p style="font-size: 8pt; margin-bottom: 0; margin: 300px 24px 30px 24px; " >
<b>All trademarks of Eclypses Inc.</b> may not be used without Eclypses Inc.'s prior written consent. No license for any use thereof has been granted without express written consent. Any unauthorized use thereof may violate copyright laws, trademark laws, privacy and publicity laws and communications regulations and statutes. The names, images and likeness of the Eclypses logo, along with all representations thereof, are valuable intellectual property assets of Eclypses, Inc. Accordingly, no party or parties, without the prior written consent of Eclypses, Inc., (which may be withheld in Eclypses' sole discretion), use or permit the use of any of the Eclypses trademarked names or logos of Eclypses, Inc. for any purpose other than as part of the address for the Premises, or use or permit the use of, for any purpose whatsoever, any image or rendering of, or any design based on, the exterior appearance or profile of the Eclypses trademarks and or logo(s).
</p>