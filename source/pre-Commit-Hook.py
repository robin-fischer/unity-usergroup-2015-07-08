#!/usr/bin/python

# The MIT License (MIT)
# 
# Copyright (c) 2015 Daedalic Entertainment GmbH
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


def command_output(cmd):
    """
    Capture a commands standard output.
    """
    import subprocess
    return subprocess.Popen(
        cmd.split(";"), stdout=subprocess.PIPE).communicate()[0]


def check_path_for_svn_property(repo_path, path, prop_name):
    """
    Check for a specific SVN Property at a given Repository Path
    """
    return command_output("/usr/bin/svnlook;propget;" + repo_path + ";" + prop_name + ";" + path)

def search_for_meta_file(file_path, start_index, file_path_list):

    # In case a Folder is added.
    if file_path.endswith("/"):
        file_path = file_path[:-1]

    for i in range(start_index, len(file_path_list)):

        next_file_name = file_path_list[i];

        if next_file_name == file_path + ".meta":
            return True

    return False

def handle_added_files(added_files, meta_counter):

    for i in range(0, len(added_files)):

        file_name = added_files[i]

        # continue if the added File is a .meta File
        if file_name.endswith(".meta"):
            continue

        # search the following files for the .meta file
        if search_for_meta_file(file_name, i, added_files):
            continue

        print("XX: File with Missing .meta:", file_name)
        # printing Error back to User
        sys.stderr.write("PRE-COMMIT-HOOK: File added without .meta: '" + file_name + "'\n")
        meta_counter += 1

    return meta_counter


def handle_deleted_files(deleted_files, meta_counter):

    for i in range(0, len(deleted_files)):

        file_name = deleted_files[i]

        #continue if the deleted File is a .meta File
        if file_name.endswith(".meta"):
            continue

        # search the following files for the .meta file.
        if search_for_meta_file(file_name, i, deleted_files):
            continue

        print("XX: File deleted without .meta:", file_name)
        # printing Error back to User
        sys.stderr.write("PRE-COMMIT-HOOK: File deleted without .meta: '" + file_name + "'\n")
        meta_counter += 1

    return meta_counter


def check_for_meta_and_add_meta(look_cmd, unityDataPath):

    def filename(line):
        return line[4:]

    def added(line):
        return line and line[0] in "A"

    def deleted(line):
        return line and line[0] in "D"

    added_files = []
    deleted_files = []

    for line in command_output(look_cmd % "changed").split("\n"):
        tmp_name = filename(line)

        print("Processing: " + tmp_name)
        if not tmp_name.startswith(unityDataPath):
            continue
        print("PASS: " + tmp_name)

        if added(line):
            added_files.append(tmp_name)
            print("XX: Added:", tmp_name)
        elif deleted(line):
            deleted_files.append(tmp_name)
            print("XX: Deleted:", tmp_name)

    if len(added_files) == 0:
        print("No Files were added.")

    if len(deleted_files) == 0:
        print("No Files were deleted.")

    if len(added_files) == 0 and len(deleted_files) == 0:
        return 0

    meta_counter = 0

    if len(added_files) > 0:
        meta_counter = handle_added_files(added_files, meta_counter)

    if len(deleted_files) > 0:
        meta_counter = handle_deleted_files(deleted_files, meta_counter)

    return meta_counter


def main():

    usage = """usage: %prog REPOS TXN

    Run pre-commit options on a repository transaction."""

    from optparse import OptionParser
    parser = OptionParser(usage=usage)
    parser.add_option("-r", "--revision",
                    help="Test mode. TXN actually refers to a revision.",
                    action="store_true", default=False)
    errors = 0

    try:

        (opts, (repos, txn_or_rvn)) = parser.parse_args()
        look_opt = ("--transaction", "--revision")[opts.revision]
        prop_output = check_path_for_svn_property(repos, ".", "unity:dataPath")
        if not prop_output:
            return 0

        print("Unity Path: "  + prop_output)

        look_cmd = "/usr/bin/svnlook;%s;%s;%s;%s" % (
            "%s", repos, look_opt, txn_or_rvn)
        errors += check_for_meta_and_add_meta(look_cmd, prop_output)
    except:
        parser.print_help()
        errors = 4
        sys.stderr.write("An Error has occurred")

    return errors

if __name__ == "__main__":
    import sys
    sys.exit(main())
