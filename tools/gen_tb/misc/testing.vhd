library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use STD.TEXTIO.ALL;

use WORK.TESTING_CONFIG.ALL;
use WORK.TESTING_COMMON.ALL;
use WORK.TESTING_INTERNAL.ALL;

package testing is
	-- testbench functions
	function set_ports(pset_vector : in STD_LOGIC_VECTOR) return STD_LOGIC_VECTOR;

	-- testbench procedures
	procedure vector_file_open(
		file_name : in STRING;
		FILE pfile : TEXT
	);

	procedure tb_begin;

	procedure tb_end(
		fail_count : in INTEGER
	);

	procedure tb_tc_header(
		testname_array : in T_TESTNAME;
		testcase_num : in INTEGER
	);

	procedure tb_tc_footer;

	procedure tb_build_filename_array(
		path : in STRING;
		component_name : in STRING;
		filename_array : out T_FILENAME
	);

	procedure init_set_vector(
		def_vector : in STD_LOGIC_VECTOR;
		teststate : in T_TESTSTATE_OPT;
		set_vector : out STD_LOGIC_VECTOR
	);

	procedure fill_vectors_from_file(
		FILE vector_file : TEXT;
		vector_num : in INTEGER;
		set_vector : inout STD_LOGIC_VECTOR;
		expect_vector : inout STD_LOGIC_VECTOR;
		eof : inout BOOLEAN;
		vector_interval : out TIME
	);

	procedure check_expectations(
		expect_vector : in STD_LOGIC_VECTOR;
		ports : in STD_LOGIC_VECTOR;
		testcase_num : in INTEGER;
		vector_num : in INTEGER;
		fail_count : inout INTEGER
	);
end testing;

package body testing is
	-- testbench functions
	function set_ports(pset_vector : in STD_LOGIC_VECTOR) return STD_LOGIC_VECTOR is
		variable ports : STD_LOGIC_VECTOR(pset_vector'REVERSE_RANGE) := (others => 'Z');
	begin
		for i in pset_vector'RANGE loop
			if pset_vector(i) = '-' then
				next;
			else
				ports(i) := pset_vector(i);
			end if;
		end loop;
		return ports;
	end set_ports;

	-- testbench procedures
	procedure vector_file_open(
		file_name : in STRING;
		FILE pfile : TEXT
	) is
		variable file_status : FILE_OPEN_STATUS;
	begin
		file_open(file_status, pfile, file_name, read_mode);
		if file_status /= OPEN_OK then
			report "FATAL ERROR: Couldn't open file: " & file_name severity failure;
		end if;
	end vector_file_open;

	procedure tb_begin is
	begin
		report "TESTBENCH STARTS";
	end tb_begin;

	procedure tb_end(
		fail_count : in INTEGER
	) is
	begin
		report "TESTBENCH FINISHED";
		report INTEGER'IMAGE(fail_count) & "/" & INTEGER'IMAGE(TESTCASE_COUNT) & " TESTCASE(S) FAILED";
	end tb_end;

	procedure tb_tc_header(
		testname_array : in T_TESTNAME;
		testcase_num : in INTEGER
	) is
	begin
		report " -----";
		report " *** (time=" & TIME'IMAGE(NOW) & ") STARTING TEST " & INTEGER'IMAGE(testcase_num) & "/" & INTEGER'IMAGE(TESTCASE_COUNT) & ": " & testname_array(testcase_num);
		report " -----";
	end tb_tc_header;

	procedure tb_tc_footer is
	begin
		report " _________________________________________________";
	end tb_tc_footer;

	procedure tb_build_filename_array(
		path : in STRING;
		component_name : in STRING;
		filename_array : out T_FILENAME
	) is
	begin
		for file_num in 1 to TESTCASE_COUNT loop
			if (file_num < 10) then
				filename_array(file_num) := path & component_name & "_0" & INTEGER'IMAGE(file_num) & ".vec";
			else
				filename_array(file_num) := path & component_name & "_" & INTEGER'IMAGE(file_num) & ".vec";
			end if;
		end loop;
	end tb_build_filename_array;

	procedure init_set_vector(
		def_vector : in STD_LOGIC_VECTOR;
		teststate : in T_TESTSTATE_OPT;
		set_vector : out STD_LOGIC_VECTOR
	) is
	begin
		if (teststate = TS_DISCARD) then
			clear_set_vector(def_vector, set_vector);
		end if;
	end init_set_vector;

	procedure fill_vectors_from_file(
		FILE vector_file : TEXT;
		vector_num : in INTEGER;
		set_vector : inout STD_LOGIC_VECTOR;
		expect_vector : inout STD_LOGIC_VECTOR;
		eof : inout BOOLEAN;
		vector_interval : out TIME
	) is
		variable vector_line : LINE;
	begin
		vector_file_readline(vector_file, vector_line, eof);
		if (eof = true) then
			return;
		end if;

		report "PROCESSING VECTOR: " & INTEGER'IMAGE(vector_num);
		update_vectors(SIGNAL_COUNT - 1, vector_line, set_vector, expect_vector);
		vector_interval := get_interval(vector_line.all);
	end fill_vectors_from_file;

	procedure check_expectations(
		expect_vector : in STD_LOGIC_VECTOR;
		ports : in STD_LOGIC_VECTOR;
		testcase_num : in INTEGER;
		vector_num : in INTEGER;
		fail_count : inout INTEGER
	) is
		variable fail : BOOLEAN;
	begin
		check_ports(expect_vector, ports, fail, testcase_num);
		if fail = true then
			report "!!! expectations are not met in vector: " & INTEGER'IMAGE(vector_num) severity error;
			fail_count := fail_count + 1;
		end if;
	end check_expectations;
end testing;
