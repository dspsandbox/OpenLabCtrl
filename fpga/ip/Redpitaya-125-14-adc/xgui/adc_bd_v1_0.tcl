# SPDX-License-Identifier: MIT
# Author: Pau Gómez (2026)
# OpenLabCtrl - FPGA-timed experiment control on Red Pitaya STEMlab 125-14

# Definitional proc to organize widgets for parameters.
proc init_gui { IPINST } {
  ipgui::add_param $IPINST -name "Component_Name"
  #Adding Page
  ipgui::add_page $IPINST -name "Page 0"


}


