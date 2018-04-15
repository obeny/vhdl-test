library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.STD_LOGIC_ARITH.ALL;
use IEEE.STD_LOGIC_UNSIGNED.ALL;

entity counter_gen is
	generic (
		N : NATURAL
	);

	port (
		clk : in STD_LOGIC;

		clr : in STD_LOGIC;
		value : in STD_LOGIC_VECTOR (N-1 downto 0);

		z : out STD_LOGIC := '0'
	);
end counter_gen;

architecture counter_gen_arch of counter_gen is
	signal s_z : STD_LOGIC := '0';
	signal count : STD_LOGIC_VECTOR (N-1 downto 0) := (others => '0');
begin
	process (clk, clr, value)
	begin
		if clr = '1' then
			s_z <= '0';
			count <= (others => '0');
		elsif rising_edge(clk) then
			if count < (value) then
				count <= count + "1";
			end if;

			if count = (value - 1) then
				s_z <= '1';
			end if;
		end if;
	end process;

	z <= s_z;
end counter_gen_arch;
