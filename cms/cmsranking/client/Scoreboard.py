# -*- coding: utf-8 -*-

# Programming contest management system
# Copyright © 2011-2012 Luca Wehrstedt <luca.wehrstedt@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from pyjamas.ui.UIObject import UIObject
from pyjamas.ui.FocusWidget import FocusWidget

from pyjamas import Window
from pyjamas import DOM

from __pyjamas__ import JS


class omni_container(object):
    def __contains__(self, a):
        return True


class Scoreboard(object):
    def __init__(self, ds, up):
        self.ds = ds
        self.up = up
        self.expanded = omni_container()

        self.tcols_el = DOM.getElementById('Scoreboard_cols')
        self.thead_el = DOM.getElementById('Scoreboard_head')
        self.tbody_el = DOM.getElementById('Scoreboard_body')

        self.ds.add_select_handler(self.select_handler)

    def make_head(self):
        result = ''
        html = '<tr>\n' \
               '    <th class="sel"></th>\n' \
               '    <th class="rank">Rank</th>\n' \
               '    <th class="f_name">First Name</th>\n' \
               '    <th class="l_name">Last Name</th>\n' \
               '    <th class="team">Team</th>\n'
        result += html

        for (c_id, contest) in self.ds.iter_contests():
            if c_id in self.expanded:
                for (t_id, task) in self.ds.iter_tasks():
                    if task['contest'] == c_id:
                        html = '    <th class="score task">' \
                               '<abbr title="%s">%s</abbr></th>'
                        result += html % (task['name'], task['name'][0])
            html = '    <th class="score contest">%s</th>'
            result += html % contest['name']

        html = '    <th class="score global">Global</th>\n' \
               '</tr>'
        result += html

        return result

    def get_score_class(self, score, max_score):
        if score == 0:
            return "score_0"
        else:
            rel_score = int(score / max_score * 10) * 10
            if rel_score == 100:
                return "score_100"
            else:
                return "score_%d_%d" % (rel_score, rel_score + 10)

    def make_row(self, u_id, user, rank, t_key=None, c_key=None):
        result = ''
        html = '<tr id="%s"%s>\n' \
               '    <td class="sel">\n' \
               '        <input type="checkbox"%s />\n' \
               '    </td>\n' \
               '    <td class="rank">%s</td>\n' \
               '    <td class="f_name">%s</td>\n' \
               '    <td class="l_name">%s</td>\n'
        result += html % (
            u_id,
            (' class="selected"' if self.ds.get_selected(u_id) else ''),
            ('checked' if self.ds.get_selected(u_id) else ''),
            rank, user['f_name'], user['l_name'])

        if user['team']:
            # FIXME: hardcoded flag path
            html = '    <td class="team">\n' \
                   '        <img src="/flags/%s" title="%s" />\n' \
                   '    </td>\n'
            result += html % (user['team'],
                              self.ds.teams[user['team']]['name'])
        else:
            html = '    <td class="team"></td>\n'
            result += html

        for (c_id, contest) in self.ds.iter_contests():
            if c_id in self.expanded:
                for (t_id, task) in self.ds.iter_tasks():
                    if task['contest'] == c_id:
                        score_class = self.get_score_class(
                            self.ds.get_score_t(u_id, t_id),
                            self.ds.tasks[t_id]['score'])
                        if t_id == t_key:
                            score_class += ' sort_key'
                        html = '    <td class="score task %s">%s</td>\n'
                        result += html % (
                            score_class,
                            round(self.ds.get_score_t(u_id, t_id), 2))
            score_class = self.get_score_class(
                self.ds.get_score_c(u_id, c_id),
                sum([task['score']
                     for task in self.ds.tasks.itervalues()
                     if task['contest'] == c_id]))
            if c_id == c_key:
                score_class += ' sort_key'
            html = '    <td class="score contest %s">%s</td>\n'
            result += html % (score_class,
                              round(self.ds.get_score_c(u_id, c_id), 2))

        score_class = self.get_score_class(
            self.ds.get_score(u_id),
            sum([task['score'] for task in self.ds.tasks.itervalues()]))
        if t_key is None and c_key is None:
            score_class += ' sort_key'
        html = '    <td class="score global %s">%s</td>\n' \
               '</tr>\n'
        result += html % (score_class, round(self.ds.get_score(u_id), 2))

        return result

    def make_body(self, t_key=None, c_key=None):
        if t_key:
            users = sorted([(-1 * self.ds.get_score_t(u_id, t_key),
                             -1 * self.ds.get_score(u_id),
                             user['l_name'], user['f_name'], u_id)
                            for (u_id, user) in self.ds.users.iteritems()])
        elif c_key:
            users = sorted([(-1 * self.ds.get_score_c(u_id, c_key),
                             -1 * self.ds.get_score(u_id),
                             user['l_name'], user['f_name'], u_id)
                            for (u_id, user) in self.ds.users.iteritems()])
        else:
            users = sorted([(-1 * self.ds.get_score(u_id),
                             -1 * self.ds.get_score(u_id),
                             user['l_name'], user['f_name'], u_id)
                            for (u_id, user) in self.ds.users.iteritems()])

        col_count = len(self.ds.contests) + \
                    len([t_id for t_id, task in self.ds.tasks.iteritems()
                         if task['contest'] in self.expanded])

        result = ''
        prev_score = None
        rank = 0
        equal = 1

        for idx, item in enumerate(users):
            if idx != 0:
                html = '<tr class="separator">\n' \
                       '    <td colspan="%s"></td>\n' \
                       '</tr>'
                result += html % (col_count + 5)

            score = -1 * item[0]
            if score == prev_score:
                equal += 1
            else:
                prev_score = score
                rank += equal
                equal = 1

            result += self.make_row(item[4], self.ds.users[item[4]],
                                    rank, t_key, c_key)

        return result

    def update(self, t_key=None, c_key=None):
        col_layout = ''
        for (c_id, contest) in self.ds.iter_contests():
            if c_id in self.expanded:
                for (t_id, task) in self.ds.iter_tasks():
                    if task['contest'] == c_id:
                        col_layout += '<col class="score task" />'
            col_layout += '<col class="score contest" />'

        head_html = self.make_head(t_key, c_key)
        body_html = self.make_body(t_key, c_key)

        DOM.setInnerHTML(self.tcols_el, col_layout)
        DOM.setInnerHTML(self.thead_el, head_html)
        DOM.setInnerHTML(self.tbody_el, body_html)

        # create callbacks for selection
        for (u_id, user) in self.ds.users.iteritems():
            row = DOM.getElementById(u_id)
            cell = DOM.getChild(row, 0)
            check = DOM.getChild(cell, 0)
            JS('''
            check.addEventListener('change', self.select_factory(u_id));
            ''')

        # create callbacks for UserPanel
        for (u_id, user) in self.ds.users.iteritems():
            row = DOM.getElementById(u_id)
            for idx in [2, 3]:
                elem = DOM.getChild(row, idx)
                widget = FocusWidget(elem)
                widget.addClickListener(self.user_callback_factory(u_id))
                DOM.setEventListener(elem, widget)

        # create callbacks for sorting
        idx = 5
        row_el = DOM.getChild(self.thead_el, 0)
        for (c_id, contest) in self.ds.iter_contests():
            if c_id in self.expanded:
                for (t_id, task) in self.ds.iter_tasks():
                    if task['contest'] == c_id:
                        elem = DOM.getChild(row_el, idx)
                        widget = FocusWidget(elem)
                        widget.addClickListener(self.sort_task_factory(t_id))
                        DOM.setEventListener(elem, widget)
                        idx += 1
            elem = DOM.getChild(row_el, idx)
            widget = FocusWidget(elem)
            widget.addClickListener(self.sort_contest_factory(c_id))
            DOM.setEventListener(elem, widget)
            idx += 1
        elem = DOM.getChild(row_el, idx)
        widget = FocusWidget(elem)
        widget.addClickListener(self.sort_global_factory())
        DOM.setEventListener(elem, widget)

    def select_handler(self, u_id, flag):
        row = DOM.getElementById(u_id)
        cell = DOM.getChild(row, 0)
        check = DOM.getChild(cell, 0)
        # FIXME classList is not supported by all browsers
        JS('''
        if (flag) {
            row.classList.add("selected")
        } else {
            row.classList.remove("selected")
        }
        check.checked = flag
        ''')

    def select_factory(self, u_id):
        def result():
            row = DOM.getElementById(u_id)
            cell = DOM.getChild(row, 0)
            check = DOM.getChild(cell, 0)
            self.ds.set_selected(u_id,
                                 DOM.getBooleanAttribute(check, 'checked'))
        return result

    def user_callback_factory(self, u_id):
        def result():
            self.up.show(u_id)
        return result

    def sort_task_factory(self, t_id):
        def result():
            self.update(t_key=t_id)
        return result

    def sort_contest_factory(self, c_id):
        def result():
            self.update(c_key=c_id)
        return result

    def sort_global_factory(self):
        def result():
            self.update()
        return result