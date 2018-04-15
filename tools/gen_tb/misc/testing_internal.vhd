library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use STD.TEXTIO.ALL;

use WORK.TESTING_CONFIG.ALL;
use WORK.TESTING_COMMON.ALL;

package testing_internal is
	-- constants
	constant CONST_VALUES_OFFSET : INTEGER := 6;

	-- functions
	function std_logic_vector2string(vector : in STD_LOGIC_VECTOR) return STRING;
	function get_interval(vector : in STRING) return TIME;

	-- procedures
	procedure vector_file_readline(
		FILE pfile : TEXT;
		pline : inout LINE;
		eof : out BOOLEAN
	);
	
	procedure clear_set_vector(
		pdefault : in STD_LOGIC_VECTOR;
		ptarget : out STD_LOGIC_VECTOR
	);

	procedure update_vectors(
		csigcount : INTEGER;
		pline : inout LINE;
		pset_vector : inout STD_LOGIC_VECTOR;
		pexpect_vector : inout STD_LOGIC_VECTOR
	);
	
	procedure check_ports(
		pexpect_vector : in STD_LOGIC_VECTOR;
		pports : in STD_LOGIC_VECTOR;
		fail : out BOOLEAN;
		testcase : INTEGER
	);

end testing_internal;

package body testing_internal is
	-- functions
	function std_logic_vector2string(vector : in STD_LOGIC_VECTOR) return STRING is
		variable result : STRING(1 to vector'LENGTH);
	begin
		for pos in vector'RANGE loop
			result(pos + 1) := STD_LOGIC'IMAGE(vector(pos))(2);
		end loop;
		return result;
	end std_logic_vector2string;
	
	function get_interval(vector : in STRING) return TIME is
		variable mul : TIME;
		variable def : INTEGER := 0;
		variable interval : STRING (1 to 4);
	begin
		interval := vector(2 to (CONST_VALUES_OFFSET - 1));
		case interval(1) is
			when 'n' => mul := 1 ns;
			when 'u' => mul := 1 us;
			when 'm' => mul := 1 ms;
			when 's' => mul := 1000 ms;
			when others => report "FATAL ERROR: Interval incorrectly defined :" & interval severity failure;
		end case;

		def := INTEGER'VALUE(interval(2 to (CONST_VALUES_OFFSET - 2)));

		return mul * def;
	end get_interval;

	-- procedures
	procedure vector_file_readline(
		FILE pfile : TEXT;
		pline : inout LINE;
		eof : out BOOLEAN
	) is
	begin
		loop
			if endfile(pfile) then
				eof := true;
				exit;
			end if;
			readline(pfile, pline);
			if pline(1) /= '#' then
				eof := false;
				exit;
			end if;
		end loop;
	end vector_file_readline;

	procedure clear_set_vector(
		pdefault : in STD_LOGIC_VECTOR;
		ptarget : out STD_LOGIC_VECTOR
	) is
	begin
		for i in ptarget'RANGE loop
			ptarget(i) := 'U';
		end loop;
		for i in ptarget'RANGE loop
			ptarget(i) := pdefault(i);
		end loop;
	end clear_set_vector;

	procedure update_vectors(
		csigcount : INTEGER;
		pline : inout LINE;
		pset_vector : inout STD_LOGIC_VECTOR;
		pexpect_vector : inout STD_LOGIC_VECTOR
	) is
		variable sig_num : INTEGER := 0;
	begin
		for i in pexpect_vector'RANGE loop
			pexpect_vector(i) := 'U';
		end loop;

		for i in CONST_VALUES_OFFSET to pline'RIGHT loop
			case pline(i) is
				when ' ' => next;
				when '-' => null;
				when 'l' => pexpect_vector(sig_num) := '0';
				when 'h' => pexpect_vector(sig_num) := '1';
				when 'L' =>
					pset_vector(sig_num) := 'Z';
					pexpect_vector(sig_num) := '0';
				when 'H' =>
					pset_vector(sig_num) := 'Z';
					pexpect_vector(sig_num) := '1';
				when 'Z' =>
					pset_vector(sig_num) := 'Z';
					pexpect_vector(sig_num) := 'Z';
				when '0' => pset_vector(sig_num) := '0';
				when '1' => pset_vector(sig_num) := '1';
				when 'X' => pexpect_vector(sig_num) := 'X';
				when others => report "FATAL ERROR: Illegal character in vector file: " & pline(i) severity failure;
			end case;
			sig_num := sig_num + 1;
			if sig_num > csigcount + 1 then
				report "FATAL ERROR: Vector contains too much values!" severity failure;
			end if;
		end loop;
		if sig_num < csigcount then
			report "FATAL ERROR: Vector contains not enough values!" severity failure;
		end if;
		
		report " => updated SET    vector: " & std_logic_vector2string(pset_vector);
		report " => updated EXPECT vector: " & std_logic_vector2string(pexpect_vector);
	end update_vectors;

	procedure check_ports(
		pexpect_vector : in STD_LOGIC_VECTOR;
		pports : in STD_LOGIC_VECTOR;
		fail : out BOOLEAN;
		testcase : INTEGER
	) is
	begin
		fail := false;
		for i in pexpect_vector'REVERSE_RANGE loop
			if pexpect_vector(i) = '0' or pexpect_vector(i) = '1' or pexpect_vector(i) = 'X' then
				if pports(i) /= pexpect_vector(i) then
					report " !!! TESTCASE: " & INTEGER'IMAGE(testcase) & " (time=" & TIME'IMAGE(NOW) & ") expected value mismatch: " &
						"vector[" & INTEGER'IMAGE(i) & "]=" & STD_LOGIC'IMAGE(pports(i)) & "; expected=" & STD_LOGIC'IMAGE(pexpect_vector(i)) severity error;
					report " => expectations: " & std_logic_vector2string(pexpect_vector) severity error;
					report " =>          got: " & std_logic_vector2string(pports) severity error;
					fail := true;
				end if;
			else
				next;
			end if;
		end loop;
	end check_ports;
end testing_internal;
