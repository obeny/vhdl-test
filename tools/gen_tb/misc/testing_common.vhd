library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use STD.TEXTIO.ALL;

use WORK.TESTING_CONFIG.ALL;

package testing_common is
	-- types
	type T_CLOCK_OPT is (CLK_DEFAULT, CLK_RESET, CLK_DISABLE);
	type T_TESTSTATE_OPT is (TS_REMEMBER, TS_DISCARD);

	type T_TESTNAME is array(0 to TESTCASE_COUNT) of STRING(1 to 128);
	type T_FILENAME is array(0 to TESTCASE_COUNT) of STRING(1 to FILENAME_LEN);

	type T_CLOCK_RESET_DISABLE is array (1 to TESTCASE_COUNT) of T_CLOCK_OPT;
	type T_TESTSTATE is array (1 to TESTCASE_COUNT) of T_TESTSTATE_OPT;
end testing_common;

package body testing_common is
end testing_common;
