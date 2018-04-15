library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

entity xor_gate is
	port (
		a : in STD_LOGIC;
		b : in STD_LOGIC;
		z : out STD_LOGIC
	);
end xor_gate;

architecture xor_gate_arch of xor_gate is
begin
	z <= a xor b;
end xor_gate_arch;
