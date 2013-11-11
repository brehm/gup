from .util import *

class TestBasicRules(TestCase):
	def setUp(self):
		super(TestBasicRules, self).setUp()
		self.write("default.gup", echo_to_target('$2'))
		self.source_contents = "Don't overwrite me!"
		self.write("source.txt", self.source_contents)

	def test_doesnt_overwrite_existing_file(self):
		self.assertRaises(Unbuildable, lambda: self.build("source.txt"))

		self.build_u("source.txt")
		self.assertEqual(self.read("source.txt"), self.source_contents)

	def test_fails_on_updating_nonexitent_file(self):
		self.assertRaises(Unbuildable, lambda: self.build_u("nonexistent.txt"))

	def test_only_creates_new_files_matching_pattern(self):
		self.assertRaises(Unbuildable, lambda: self.build("output.txt"))

		self.write("Gupfile", "default.gup:\n\toutput.txt\n\tfoo.txt")
		self.build("output.txt")
		self.build("foo.txt")
		self.assertEqual(self.read("output.txt"), "output.txt")

		self.write("Gupfile", "default.gup:\n\tf*.txt")
		self.assertRaises(Unbuildable, lambda: self.build("output.txt"))
		self.build("foo.txt")
		self.build("far.txt")

	def test_exclusions(self):
		self.write("Gupfile", "default.gup:\n\t*.txt\n\n\t!source.txt")
		self.build("output.txt")
		self.assertRaises(Unbuildable, lambda: self.build("source.txt"))
		self.assertEqual(self.read("source.txt"), self.source_contents)

class TestGupdirectory(TestCase):
	def test_gupdir_is_search_target(self):
		self.write("gup/base.gup", '#!/bin/bash\necho -n "base" > "$1"')
		self.build('base')
		self.assertEqual(self.read('base'), 'base')
	
	def test_multiple_gup_dirs_searched(self):
		self.write("a/gup/b/c.gup", echo_to_target('c'))
		# shadowed by the above rule
		self.write("gup/a/b/c.gup", echo_to_target('wrong c'))

		self.write("gup/a/b/d.gup", echo_to_target('d'))

		self.build_assert('a/b/c', 'c')
		self.build_assert('a/b/d', 'd')

	def test_patterns_match_against_path_from_gupfile(self):
		self.write("a/default.gup", echo_to_target('ok'))
		self.write("a/Gupfile", 'default.gup:\n\tb/*/d')

		self.build_assert('a/b/c/d', 'ok')
		self.build_assert('a/b/xyz/d', 'ok')
		self.assertRaises(Unbuildable, lambda: self.build("x/b/cd"))
	
	def test_leaves_nothing_for_unbuildable_target(self):
		self.assertRaises(Unbuildable, lambda: self.build("a/b/c/d"))
		self.assertEquals(os.listdir(self.ROOT), [])

	def test_gupfile_patterns_ignore_gup_dir(self):
		self.write("gup/a/default.gup", echo_to_target('ok'))
		self.write("gup/a/Gupfile", 'default.gup:\n\tb/*/d')

		self.build_assert('a/b/c/d', 'ok')
		self.build_assert('a/b/xyz/d', 'ok')
		self.assertRaises(Unbuildable, lambda: self.build("x/b/cd"))
	
	def test_gupfile_may_specify_a_non_local_script(self):
		self.write("gup/a/default.c.gup", echo_to_target('$2, called from $(basename "$(pwd)")'))
		self.write('gup/a/b/Gupfile', '../default.c.gup:\n\t*.c')

		self.assertRaises(Unbuildable, lambda: self.build('a/foo.c'))
		self.build_assert('a/b/foo.c', 'b/foo.c, called from a')