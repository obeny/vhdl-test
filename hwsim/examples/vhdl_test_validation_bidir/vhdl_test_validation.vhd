library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

entity vhdl_test_validation_bidir is
	port (
		dir : in STD_LOGIC;
		a : inout STD_LOGIC;
		b : inout STD_LOGIC
	);
end vhdl_test_validation_bidir;

architecture vhdl_test_validation_arch of vhdl_test_validation_bidir is
	component bidir is
	port (
		dir : in STD_LOGIC;
		a : inout STD_LOGIC;
		b : inout STD_LOGIC
	);
	end component;

begin
	u_bidir: bidir
	port map(
		dir => dir,
		a => a,
		b => b
	);
end vhdl_test_validation_arch;
