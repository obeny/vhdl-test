library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

entity vhdl_test_validation_hiz is
	port (
		oe : in STD_LOGIC;
		a : in STD_LOGIC;
		b : inout STD_LOGIC
	);
end vhdl_test_validation_hiz;

architecture vhdl_test_validation_arch of vhdl_test_validation_hiz is
	component hiz_out is
	port (
		oe : in STD_LOGIC;
		a : in STD_LOGIC;
		b : inout STD_LOGIC
	);
	end component;

begin
	u_hiz_out: hiz_out
	port map(
		oe => oe,
		a => a,
		b => b
	);
end vhdl_test_validation_arch;
