# -*- coding: utf-8 -*-
import sublime, sublime_plugin
import os
import re
import codecs

class CucumberBaseCommand(sublime_plugin.WindowCommand, object):
  def __init__(self, window):
    sublime_plugin.WindowCommand.__init__(self, window)
    self.load_settings()

  def load_settings(self):
    self.settings = sublime.load_settings("CucumberStepFinder.sublime-settings")
    self.features_path = self.settings.get('cucumber_features_path')  # Default is "features"
    self.step_pattern = self.settings.get('cucumber_step_pattern')    # Default is '.*_steps.*\.rb'

  def find_all_steps(self):
    pattern = re.compile(r'((.*)(\/\^.*))\$\/')
    self.steps = []
    folders = self.window.folders()
    for folder in folders:
      for path in os.listdir(folder) + ['.']:
        full_path = os.path.join(folder, path)
        if path == self.features_path:
          self.step_files = []
          for root, dirs, files in os.walk(full_path):
            for f_name in files:
              if re.match(self.step_pattern, f_name):
                self.step_files.append((f_name, os.path.join(root, f_name)))
                step_file_path = os.path.join(root, f_name)
                with codecs.open(step_file_path, encoding='utf-8') as f:
                  index = 0
                  for line in f:
                    match = re.match(pattern, line)
                    if match:
                      self.steps.append((match.group(), index, step_file_path))
                    index += 1

  def step_found(self, index):
    if index >= 0:
      file_path = self.steps[index][2]
      view = self.window.open_file(file_path)
      self.active_ref = (view, self.steps[index][1])
      self.mark_step()

  def mark_step(self):

    view = self.window.active_view()

    if view.is_loading():
      sublime.set_timeout(self.mark_step, 50)
    else:
      view.run_command("goto_line", {"line": self.active_ref[1]+1} )

class MatchStepCommand(CucumberBaseCommand):
  def __init__(self, window):
    CucumberBaseCommand.__init__(self, window)
    self.words = self.settings.get('cucumber_code_keywords')

  def run(self, file_name=None):
    self.get_line()

  def get_line(self):
    view = self.window.active_view()
    line_sel = view.line(view.sel()[0])
    text_line = view.substr(line_sel).strip()
    self.cut_words(text_line)

  def cut_words(self, text):
     upcased = [up.capitalize() for up in self.words]
     expression = "^{0}".format('|^'.join(upcased))

     pattern = re.compile(expression)
     short_text = re.sub(pattern, '', text).strip()
     self.find_all_steps()

     step_filter = re.compile(r'.*\/\^(.*)\$\/') # map all steps
     steps_regex = [re.match(step_filter, x[0]).group(1) for x in self.steps]

     for step in self.steps:
       step_pattern = re.match(step_filter, step[0]).group(1)
       step_regex = re.compile(step_pattern)
       match =  re.match(step_regex, short_text)
       if match:
         index =  self.steps.index(step)
         self.step_found(index)
       else:
        sublime.status_message('Can\'t find a match')

class CucumberStepFinderCommand(CucumberBaseCommand):
  def __init__(self, window):
    CucumberBaseCommand.__init__(self, window)

  def run(self, file_name=None):
    self.list_steps()

  def list_steps(self):
    self.find_all_steps()
    steps_only = [x[0] for x in self.steps]
    self.window.show_quick_panel(steps_only, self.step_found)
