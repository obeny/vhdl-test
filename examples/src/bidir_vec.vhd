library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

entity bidir_vec is
	port (
		dir : in STD_LOGIC;

		a : inout STD_LOGIC_VECTOR (1 downto 0);
		b : inout STD_LOGIC_VECTOR (1 downto 0)
	);
end bidir_vec;

architecture bidir_vec_arch of bidir_vec is
	signal s_a_out : STD_LOGIC_VECTOR (1 downto 0) := (others => 'Z');
	signal s_b_out : STD_LOGIC_VECTOR (1 downto 0) := (others => 'Z');
begin
	s_a_out <= b when dir = '0';
	s_b_out <= a when dir = '1';

	a <= s_a_out when dir = '0' else (others => 'Z');
	b <= s_b_out when dir = '1' else (others => 'Z');
end bidir_vec_arch;
