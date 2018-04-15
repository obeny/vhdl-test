library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

entity complex is
	port (
		s : in STD_LOGIC;

		a : in STD_LOGIC;
		b : in STD_LOGIC;

		z : out STD_LOGIC
	);
end complex;

architecture complex_arch of complex is
	component and_gate
	port (
		a : in STD_LOGIC;
		b : in STD_LOGIC;
		z : out STD_LOGIC
	);
	end component;

	component xor_gate
	port (
		a : in STD_LOGIC;
		b : in STD_LOGIC;
		z : out STD_LOGIC
	);
	end component;

	signal s_a : STD_LOGIC := '0';
	signal s_b : STD_LOGIC := '0';
	signal s_and_gate_z : STD_LOGIC := '0';
	signal s_xor_gate_z : STD_LOGIC := '0';

begin
	u_and_gate: and_gate
	port map(
		a => s_a,
		b => s_b,
		z => s_and_gate_z
	);

	u_xor_gate: xor_gate
	port map(
		a => s_a,
		b => s_b,
		z => s_xor_gate_z
	);

	s_a <= a;
	s_b <= b;
	z <= s_and_gate_z when s = '0' else s_xor_gate_z;
end complex_arch;
