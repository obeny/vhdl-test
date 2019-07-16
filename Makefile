# import configuration
include Makefile.cnf

# MISC
# ====

# color definitions for unix
ifneq ($(COLORS),no)
C_BLUE=\033[1;34m
C_GREEN=\033[1;32m
C_RED=\033[1;31m
C_YELLOW=\033[1;33m
C_NC=\033[0m
C_WHITE=\033[1;037m
endif

# select targets to build
ifeq ($(USE_SIM),yes)
SIM_TARGET=sim

ifneq ($(XILINX_X86_64),no)
XILINX_LIN=lin64
else
XILINX_LIN=lin
endif
endif

ifeq ($(USE_HW),yes)
HW_TARGET=hw
endif

# TOOLS
# =====

# XML validation
XMLLINT=xmllint
XMLLINT_OPTS=--noout --schema testbench.xsd

# testbench generator
GEN_TB=tools/gen_tb/gen_tb
GEN_TB_OPTS=--verbose

# Xilinx
FUSE=$(XILINX_ISE_DIR)/bin/$(XILINX_LIN)/fuse
FUSE_OPTS=--incremental --nodebug --ise default --rangecheck --timeprecision_vhdl 1ns

# GLOBALS
# =======

# available testcases
TBS=$(subst tb/,,$(subst .xml,,$(wildcard tb/*.xml)))
DEPS_DIR=.deps
LOGS_DIR=logs
TARGET_SIM_DIR=target_sim
TARGET_HW_DIR=target_hw

# TARGETS
# =======

all: $(SIM_TARGET) $(HW_TARGET)

# XML syntax checking
# -------------------
XML_CHECK_TARGETS=$(addprefix $(DEPS_DIR)/xml_check_,$(TBS))

$(DEPS_DIR)/xml_check_%: tb/%.xml
	@mkdir -p $(dir $@)
	@echo -e "$(C_BLUE)[XML VALID]$(C_NC) Validating testbench XML input for: $(C_WHITE)$<$(C_NC)"
	@$(XMLLINT) $(XMLLINT_OPTS) $<
	@touch $@

xml_check: $(XML_CHECK_TARGETS)

# GENERATE SIM
# ------------
# generating VHD files
SIM_GEN_TARGETS=$(addprefix $(TARGET_SIM_DIR)/,$(addsuffix _tb.vhd,$(TBS)))
GEN_TB_VHD_TARGET=--target=vhdl

$(TARGET_SIM_DIR)/%_tb.vhd: tb/%.xml $(DEPS_DIR)/xml_check_%
	@mkdir -p $(dir $@)
	@echo -e "$(C_YELLOW)[VHD GEN]$(C_NC) Generating VHDL testbench for: $(C_WHITE)$<$(C_NC) => $(C_WHITE)$@$(C_NC)"
	@$(GEN_TB) $(GEN_TB_OPTS) $(GEN_TB_VHD_TARGET) --out=$@ --scripts=$(TB_GEN_SCRIPT_DIR) $<

sim_vhd: xml_check $(SIM_GEN_TARGETS)

# adding testing.vhd
$(TARGET_SIM_DIR)/testing.vhd:
	@echo -e "$(C_YELLOW)[TESTING VHD]$(C_NC) Linking testing VHD module: $(C_WHITE)testing.vhd$(C_NC)"
	@if [ ! -L $@ ]; then ln -s ../tools/gen_tb/misc/testing.vhd $@; fi

# adding testing_common.vhd
$(TARGET_SIM_DIR)/testing_common.vhd:
	@echo -e "$(C_YELLOW)[TESTING_COMMON VHD]$(C_NC) Linking testing_common VHD module: $(C_WHITE)testing_common.vhd$(C_NC)"
	@if [ ! -L $@ ]; then ln -s ../tools/gen_tb/misc/testing_common.vhd $@; fi

# adding testing_internal.vhd
$(TARGET_SIM_DIR)/testing_internal.vhd:
	@echo -e "$(C_YELLOW)[TESTING_INTERNAL VHD]$(C_NC) Linking testing_internal VHD module: $(C_WHITE)testing_internal.vhd$(C_NC)"
	@if [ ! -L $@ ]; then ln -s ../tools/gen_tb/misc/testing_internal.vhd $@; fi

# generating project files
SIM_PRJ_TARGETS=$(addprefix $(TARGET_SIM_DIR)/,$(addsuffix _tb.prj,$(TBS)))

$(TARGET_SIM_DIR)/%_tb.prj: $(TARGET_SIM_DIR)/%_tb.vhd\
	$(TARGET_SIM_DIR)/testing_common.vhd $(TARGET_SIM_DIR)/testing_internal.vhd $(TARGET_SIM_DIR)/testing.vhd
	@echo -e "$(C_YELLOW)[PRJ GEN]$(C_NC) Generating project for: $(C_WHITE)$<$(C_NC) => $(C_WHITE)$@$(C_NC)"

	@NAME="$(subst _tb.prj,,$(subst $(TARGET_SIM_DIR)/,,$@))"; \
		truncate -s0  $@; \
		while read DEP; do \
			echo "vhdl work $${DEP}.vhd" >> $@; \
			if [ ! -L $${DEP}.vhd ]; then ln -snf ../src/$${DEP}.vhd $(TARGET_SIM_DIR)/$${DEP}.vhd; fi; \
		done < $(TARGET_SIM_DIR)/$${NAME}_tb.dep; \
		echo -e "vhdl work $${NAME}_testing_config.vhd\nvhdl work testing_common.vhd\nvhdl work testing_internal.vhd\nvhdl work testing.vhd\n" >> $@; \
		echo -e "vhdl work $${NAME}.vhd\nvhdl work $${NAME}_tb.vhd\n" >> $@; \
		if [ ! -L $${NAME}.vhd ]; then ln -snf ../src/$${NAME}.vhd $(TARGET_SIM_DIR)/$${NAME}.vhd; fi

sim_prj: $(SIM_PRJ_TARGETS)

# compiling simulation
SIM_EXE_TARGETS=$(addprefix $(TARGET_SIM_DIR)/,$(addsuffix .exe,$(TBS)))

$(TARGET_SIM_DIR)/%.exe: $(TARGET_SIM_DIR)/%_tb.prj
	@echo -e "$(C_YELLOW)[FUSE]$(C_NC) Compiling simulation for: $(C_WHITE)$<$(C_NC) => $(C_WHITE)$@$(C_NC)"

	@NAME="$(subst .exe,,$(subst $(TARGET_SIM_DIR)/,,$@))"; \
		mkdir -p "$(TARGET_SIM_DIR)/$${NAME}"; cd $(TARGET_SIM_DIR)/$${NAME}; \
		$(FUSE) $(FUSE_OPTS) "$${NAME}_tb" -prj "../$${NAME}_tb.prj" -o "../$${NAME}.exe"

sim_exe: $(SIM_EXE_TARGETS)

# run test
SIM_RUN_TARGETS=$(addprefix sim_run_,$(TBS))

sim_run_%: $(TARGET_SIM_DIR)/%.exe
	@echo -n -e "$(C_GREEN)[SIM]$(C_NC) running test: $(C_WHITE)$<$(C_NC) ... "

	@-NAME="$(subst sim_run_,,$@)"; \
		cd $(TARGET_SIM_DIR)/$${NAME}; \
		RUNTEST_RES=`../../tools/runtest_isim.sh ../$${NAME}.exe ../$${NAME}_tb.cmd ../../$(LOGS_DIR) && echo ok || echo nok`; \
		[[ "$${RUNTEST_RES}" == "ok" ]] && echo -e "$(C_GREEN)OK$(C_NC)" || echo -e "$(C_RED)FAIL$(C_NC)"; \
		[[ "$${RUNTEST_RES}" == "ok" ]] || cat ../../$(LOGS_DIR)/$${NAME}.err

sim_run: $(SIM_RUN_TARGETS)

# run test in GUI
sim_run_gui_%: $(TARGET_SIM_DIR)/%.exe
	@echo -e "$(C_RED)[GUI]$(C_NC) running test in GUI: $(C_WHITE)$<$(C_NC)"

	@NAME="$(subst .exe,,$(subst $(TARGET_SIM_DIR)/,,$<))"; \
		cd $(TARGET_SIM_DIR)/$${NAME}; \
		../$${NAME}.exe -tclbatch ../$${NAME}_tb.cmd -gui

# GENERIC TARGETS
# ---------------
sim: sim_run
hw:
	@echo "NOT YET AVAILABLE"

clean:
	rm -rf target_sim target_hw $(DEPS_DIR) $(LOGS_DIR)

clean_all: clean
	$(shell cd hwsim/platforms/stm32_maple_mini; make clean)

dist_clean: clean_all
	rm -rf scripts/* tb/* src/* hwsim/platforms/stm32_maple_mini/lib_stm32

.PHONY: all clean clean_all dist_clean  xml_check sim_testing sim_vhd sim_prj sim_exe sim sim_run_% sim_run_gui_% hw
