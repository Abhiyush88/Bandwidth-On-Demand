# Bandwidth-On-Demand
This Project focuses on Web-Application based service which can control/assign the bandwidth of a Virtual Network based on Mininet using RYU as the SDN Controller.


Project Description:
---------------------
The Architecture of the Application involves a Web GUI (Graphical User Interface) using Flask where the user can enter the parameters(MAC Address of the host, minimum and maximum bandwidth) according the dynamic nature of the network which gets translated to the SDN Controller(RYU) via its Northbound API’s which then translates the request into appropriate changes in the OVSDB Server(Database engine) via its Northbound plugin.


Project Environment:
---------------------
RYU Controller (Python-based open source SDN controller), OpenFlow protocol, OVSDB (OpenvSwitch Database), Python 2.7, Mininet, Oracle VirtualBox, Apache Flask, HTML, CSS
