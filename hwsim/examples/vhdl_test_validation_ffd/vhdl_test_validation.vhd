library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

entity vhdl_test_validation_ffd is
	port (
		clk : in STD_LOGIC;
		rst : in STD_LOGIC;
		d : in STD_LOGIC;
		q : out STD_LOGIC
	);
end vhdl_test_validation_ffd;

architecture vhdl_test_validation_arch of vhdl_test_validation_ffd is
	component ff_d is
	port (
		clk : in STD_LOGIC;
		rst : in STD_LOGIC;
		d : in STD_LOGIC;
		q : out STD_LOGIC
	);
	end component;

begin
	u_ff_d: ff_d
	port map(
		clk => clk,
		rst => rst,
		d => d,
		q => q
	);
end vhdl_test_validation_arch;
