from .util import *
class TestScripts(TestCase):

	@unittest.skipIf(IS_WINDOWS, 'posix')
	def test_interpreter(self):
		self.write('gup/all.gup', '#!./build abc\n# ...')
		self.write('gup/build', '#!/bin/bash\nset -eu\n' + '(echo "target: $4"; echo "arg: $1") > "$3"')
		os.chmod(self.path('gup/build'), 0o755)

		self.build('all')

		self.assertEquals(self.read('all'), 'target: all\narg: abc')

	def test_target_name_is_relative_to_gupfile_without_gup_dir(self):
		mkdirp(self.path('a/b'))
		self.write("gup/a/default.gup", echo_to_target('$2'))
		self.write("gup/a/nested/default.gup", echo_to_target('nested: $2'))
		self.write("gup/a/Gupfile", 'default.gup:\n\tb/c\nnested/default.gup:\n\tb/d')

		self.build('c', 'd', cwd='a/b')
		self.assertEquals(self.read('a/b/c'), os.path.join('b', 'c'))
		self.assertEquals(self.read('a/b/d'), 'nested: ' + os.path.join('..', 'b', 'd'))
	
	def test_cwd_is_relative_to_target(self):
		self.write('gup/all.gup', BASH + 'mkdir -p foo; cd foo; gup -u bar')
		self.write('gup/foo/bar.gup', echo_to_target('ok'))

		self.build('all')

		self.assertEquals(self.read('foo/bar'), 'ok')

	def test_cwd_is_relative_to_matched_target_name_from_gupfile(self):
		mkdirp(self.path('a/b'))
		self.write("a/bc.gup", BASH + 'gup -u b/d; echo -n "$(basename $(pwd))" > $1')
		self.write("a/bd.gup", BASH + 'echo -n "$(basename $(pwd))" > $1')
		self.write("a/Gupfile", 'bc.gup:\n\tb/c\nbd.gup:\n\tb/d')

		self.build('c', cwd='a/b')
		self.assertEquals(self.read('a/b/c'), 'a')
		self.assertEquals(self.read('a/b/d'), 'a')
	
	def test_self_dependency_is_detected(self):
		self.write('foo.gup', BASH + 'echo ok > "$1"; gup -u foo')
		self.assertRaises(SafeError, lambda: self.build('foo'))

	def test_directory_script_is_re_run_if_dependencies_change(self):
		self.write('dir.gup', BASH + 'gup -u file; mkdir -p "$2"; cp file "$2/"')
		self.write('file', 'filecontents')

		self.build('dir')
		self.assertTrue(os.path.isdir(self.path('dir')))
		self.assertEquals(self.read('dir/file'), 'filecontents')

		self.write('file', 'filecontents2')
		self.build_u('dir')
		self.assertEquals(self.read('dir/file'), 'filecontents2')

	def test_running_a_directory_build_script_can_replace_output_with_a_file(self):
		self.write('dir.gup', BASH + 'mkdir "$2"; echo 1 > $2/file')

		self.build('dir')
		self.assertTrue(os.path.isdir(self.path('dir')))

		self.write('dir.gup', echo_to_target('file_now'))
		self.build_u('dir')

		self.assertFalse(os.path.isdir(self.path('dir')))
		self.assertEquals(self.read('dir'), 'file_now')
	
	def _output_files(self):
		meta_files = os.listdir(self.path('.gup'))
		meta_files = filter(lambda f: not (f.endswith('.lock') or f.endswith('.deps')), meta_files)
		return list(meta_files)

	def test_cleans_up_file_if_build_fails(self):
		self.write('file.gup', BASH + 'echo hello > "$1"; exit 1')
		self.assertRaises(SafeError, lambda: self.build('file'))
		self.assertEquals(self._output_files(), [])

	def test_cleans_up_directory_if_build_fails(self):
		self.write('dir.gup', BASH + 'mkdir "$1"; echo hello > "$1"/file; exit 1')
		self.assertRaises(SafeError, lambda: self.build('dir'))
		self.assertEquals(self._output_files(), [])
	
	def test_rebuild_symlink_to_directory(self):
		self.mkdirp('dir')
		self.touch('dir/1')
		self.touch('dir/2')

		self.write('link.gup', BASH + 'ln -s dir "$1"')
		self.build('link')
		self.build('link')
		self.assertTrue(os.path.islink(self.path('link')))
		self.assertTrue(os.path.isdir(self.path('dir')))
	
	def test_cleans_up_symlink_to_directory_if_build_fails(self):
		self.write('link.gup', BASH + 'mkdir dir; touch dir/1 dir/2; ln -s "$(pwd)/dir" "$1"; exit 1')
		self.assertRaises(SafeError, lambda: self.build('link'))
		# should only remove _symlink_ - not actual contents
		self.assertTrue(os.path.exists(self.path('dir/1')))
		self.assertTrue(os.path.exists(self.path('dir/2')))

	def test_moves_broken_symlink_if_build_succeeds(self):
		self.write('link.gup', BASH + 'ln -s NOT_HERE "$1"')
		self.build('link')
		self.assertTrue(os.path.islink(self.path('link')))
		self.assertEquals(self._output_files(), [])

	def test_cleans_up_broken_symlink_if_build_fails(self):
		self.write('target.gup', BASH + 'ln -s NOT_HERE "$1"; exit 1')
		self.assertRaises(SafeError, lambda: self.build('target'))
		self.assertEquals(self._output_files(), [])
	
	@unittest.skipIf(IS_WINDOWS, 'irrelevant on windows')
	def test_permissions_of_tempfile_are_maintained(self):
		self.write('hello.gup', BASH + 'echo -e "#!/bin/bash\necho ok" > "$1"; chmod a+x "$1"')
		self.build('hello')
		out = subprocess.check_output(self.path('hello'))
		self.assertEquals(out.strip().decode('ascii'), 'ok')
