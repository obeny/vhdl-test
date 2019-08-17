library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

entity vhdl_test_validation_cnt is
	port (
		clk : in STD_LOGIC;
		clr : in STD_LOGIC;
		value : in STD_LOGIC_VECTOR (1 downto 0);
		z : out STD_LOGIC
	);
end vhdl_test_validation_cnt;

architecture vhdl_test_validation_arch of vhdl_test_validation_cnt is
	component counter_gen is
	generic (
		N : NATURAL
	);
	port (
		clk : in STD_LOGIC;
		clr : in STD_LOGIC;
		value : in STD_LOGIC_VECTOR (N-1 downto 0);
		z : out STD_LOGIC
	);
	end component;

begin
	u_counter_gen: counter_gen
	generic map(
		N => 2
	)
	port map(
		clk => clk,
		clr => clr,
		value => value,
		z => z
	);
end vhdl_test_validation_arch;
