library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

entity mux is
	port (
		s : in STD_LOGIC;

		a : in STD_LOGIC_VECTOR (0 to 3);
		b : in STD_LOGIC_VECTOR (0 to 3);

		z : out STD_LOGIC_VECTOR (0 to 3) := "0000"
	);
end mux;

architecture mux_arch of mux is
begin
	z <= a when s = '0' else b;
end mux_arch;
