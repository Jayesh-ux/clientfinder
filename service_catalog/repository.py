"""Repository for the CLIENTFINDER catalog tables (sqlite3, stdlib)."""

import json
import sqlite3

from .db import connect, row_to_dict, rows_to_list


def _rows_to_list(rows):
    return rows_to_list(rows)


def _row_to_dict(row):
    return row_to_dict(row)


def _load_json(value, default=None):
    if value is None:
        return default if default is not None else None
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return default


# ---------------------------------------------------------------- capabilities

def list_capabilities(active_only=True):
    conn = connect()
    try:
        q = "SELECT * FROM capabilities"
        if active_only:
            q += " WHERE is_active = 1"
        q += " ORDER BY category, name"
        rows = conn.execute(q).fetchall()
        return _rows_to_list(rows)
    finally:
        conn.close()


def get_capability(capability_id):
    conn = connect()
    try:
        return _row_to_dict(conn.execute(
            "SELECT * FROM capabilities WHERE id = ?", (capability_id,)).fetchone())
    finally:
        conn.close()


def get_capability_by_slug(slug):
    conn = connect()
    try:
        return _row_to_dict(conn.execute(
            "SELECT * FROM capabilities WHERE slug = ?", (slug,)).fetchone())
    finally:
        conn.close()


def create_capability(data):
    conn = connect()
    try:
        conn.execute(
            "INSERT INTO capabilities (slug, name, category, description, proficiency,"
            " verification_level, evidence_id, proven_note, is_active)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (data["slug"], data["name"], data["category"], data.get("description", ""),
             data.get("proficiency", "intermediate"),
             data.get("verification_level", "unvalidated"),
             data.get("evidence_id"), data.get("proven_note"),
             1 if data.get("is_active", True) else 0))
        conn.commit()
        return get_capability(conn.execute("SELECT last_insert_rowid()").fetchone()[0])
    finally:
        conn.close()


def update_capability(capability_id, fields):
    conn = connect()
    try:
        allowed = {"name", "category", "description", "proficiency",
                   "verification_level", "evidence_id", "proven_note", "is_active"}
        sets = []
        values = []
        for key, value in fields.items():
            if key not in allowed or value is None:
                continue
            if key == "is_active":
                value = 1 if value else 0
            sets.append(f"{key} = ?")
            values.append(value)
        if not sets:
            return get_capability(capability_id)
        sets.append("updated_at = datetime('now')")
        values.append(capability_id)
        conn.execute(f"UPDATE capabilities SET {', '.join(sets)} WHERE id = ?", values)
        conn.commit()
        return get_capability(capability_id)
    finally:
        conn.close()


def delete_capability(capability_id):
    conn = connect()
    try:
        cur = conn.execute("DELETE FROM capabilities WHERE id = ?", (capability_id,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


# ---------------------------------------------------------------- evidence

def list_evidence(verified_only=False):
    conn = connect()
    try:
        q = "SELECT * FROM portfolio_evidence"
        if verified_only:
            q += " WHERE verified = 1"
        q += " ORDER BY project_name"
        rows = conn.execute(q).fetchall()
        return _rows_to_list(rows)
    finally:
        conn.close()


def get_evidence(evidence_id):
    conn = connect()
    try:
        return _row_to_dict(conn.execute(
            "SELECT * FROM portfolio_evidence WHERE id = ?", (evidence_id,)).fetchone())
    finally:
        conn.close()


def create_evidence(data):
    conn = connect()
    try:
        cur = conn.execute(
            "INSERT INTO portfolio_evidence (project_name, role, description, skills_used,"
            " url, date_label, outcome, provenance, verified)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (data["project_name"], data.get("role"), data.get("description", ""),
             json.dumps(data.get("skills_used") or []),
             data.get("url"), data.get("date_label"), data.get("outcome"),
             data.get("provenance", "reported"), 1 if data.get("verified") else 0))
        conn.commit()
        return get_evidence(cur.lastrowid)
    finally:
        conn.close()


def update_evidence(evidence_id, fields):
    conn = connect()
    try:
        allowed = {"project_name", "role", "description", "skills_used", "url",
                   "date_label", "outcome", "provenance", "verified"}
        sets = []
        values = []
        for key, value in fields.items():
            if key not in allowed or value is None:
                continue
            if key == "skills_used":
                value = json.dumps(value or [])
            elif key == "verified":
                value = 1 if value else 0
            sets.append(f"{key} = ?")
            values.append(value)
        if not sets:
            return get_evidence(evidence_id)
        sets.append("updated_at = datetime('now')")
        values.append(evidence_id)
        conn.execute(f"UPDATE portfolio_evidence SET {', '.join(sets)} WHERE id = ?", values)
        conn.commit()
        return get_evidence(evidence_id)
    finally:
        conn.close()


def delete_evidence(evidence_id):
    conn = connect()
    try:
        cur = conn.execute("DELETE FROM portfolio_evidence WHERE id = ?", (evidence_id,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


# ---------------------------------------------------------------- solutions

def _hydrate_solution(conn, row):
    if row is None:
        return None
    sol = dict(row)
    sol["deliverables"] = _load_json(sol.get("deliverables"), []) or []
    cap_rows = conn.execute(
        "SELECT c.id, c.slug, c.name, c.category, c.proficiency, c.verification_level,"
        " c.is_active"
        " FROM capabilities c JOIN solution_capabilities sc ON sc.capability_id = c.id"
        " WHERE sc.solution_id = ? ORDER BY c.name", (sol["id"],)).fetchall()
    ev_rows = conn.execute(
        "SELECT e.* FROM portfolio_evidence e JOIN solution_evidence se ON se.evidence_id = e.id"
        " WHERE se.solution_id = ? ORDER BY e.project_name", (sol["id"],)).fetchall()
    sol["capabilities"] = _rows_to_list(cap_rows)
    sol["evidence"] = _rows_to_list(ev_rows)
    return sol


def list_solutions(active_only=True):
    conn = connect()
    try:
        q = "SELECT * FROM solution_templates"
        if active_only:
            q += " WHERE is_active = 1"
        q += " ORDER BY name"
        rows = conn.execute(q).fetchall()
        return [_hydrate_solution(conn, r) for r in rows]
    finally:
        conn.close()


def get_solution(solution_id):
    conn = connect()
    try:
        return _hydrate_solution(conn, conn.execute(
            "SELECT * FROM solution_templates WHERE id = ?", (solution_id,)).fetchone())
    finally:
        conn.close()


def get_solution_by_slug(slug):
    conn = connect()
    try:
        return _hydrate_solution(conn, conn.execute(
            "SELECT * FROM solution_templates WHERE slug = ?", (slug,)).fetchone())
    finally:
        conn.close()


def create_solution(data):
    conn = connect()
    try:
        cur = conn.execute(
            "INSERT INTO solution_templates (slug, name, summary, problem_text, deliverables,"
            " typical_effort_label, is_active)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (data["slug"], data["name"], data.get("summary"), data.get("problem_text"),
             json.dumps(data.get("deliverables") or []),
             data.get("typical_effort_label"), 1 if data.get("is_active", True) else 0))
        solution_id = cur.lastrowid
        _set_solution_capabilities(conn, solution_id, data.get("capability_slugs") or [])
        _set_solution_evidence(conn, solution_id, data.get("evidence_ids") or [])
        conn.commit()
        return get_solution(solution_id)
    finally:
        conn.close()


def update_solution(solution_id, fields):
    conn = connect()
    try:
        allowed = {"name", "summary", "problem_text", "deliverables",
                   "typical_effort_label", "is_active"}
        sets = []
        values = []
        for key, value in fields.items():
            if key not in allowed or value is None:
                continue
            if key == "deliverables":
                value = json.dumps(value or [])
            elif key == "is_active":
                value = 1 if value else 0
            sets.append(f"{key} = ?")
            values.append(value)
        if sets:
            sets.append("updated_at = datetime('now')")
            values.append(solution_id)
            conn.execute(f"UPDATE solution_templates SET {', '.join(sets)} WHERE id = ?", values)
        if fields.get("capability_slugs") is not None:
            _set_solution_capabilities(conn, solution_id, fields["capability_slugs"])
        if fields.get("evidence_ids") is not None:
            _set_solution_evidence(conn, solution_id, fields["evidence_ids"])
        conn.commit()
        return get_solution(solution_id)
    finally:
        conn.close()


def delete_solution(solution_id):
    conn = connect()
    try:
        cur = conn.execute("DELETE FROM solution_templates WHERE id = ?", (solution_id,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def _set_solution_capabilities(conn, solution_id, slug_list):
    conn.execute("DELETE FROM solution_capabilities WHERE solution_id = ?", (solution_id,))
    for slug in slug_list:
        row = conn.execute("SELECT id FROM capabilities WHERE slug = ?", (slug,)).fetchone()
        if row:
            conn.execute(
                "INSERT OR IGNORE INTO solution_capabilities (solution_id, capability_id)"
                " VALUES (?, ?)", (solution_id, row["id"]))


def _set_solution_evidence(conn, solution_id, evidence_id_list):
    conn.execute("DELETE FROM solution_evidence WHERE solution_id = ?", (solution_id,))
    for ev_id in evidence_id_list:
        conn.execute(
            "INSERT OR IGNORE INTO solution_evidence (solution_id, evidence_id)"
            " VALUES (?, ?)", (solution_id, ev_id))


# ---------------------------------------------------------------- problem patterns

def list_problem_patterns(active_only=True):
    conn = connect()
    try:
        q = ("SELECT p.*, s.name AS solution_name, s.slug AS solution_slug"
             " FROM problem_patterns p"
             " JOIN solution_templates s ON s.id = p.solution_id")
        if active_only:
            q += " WHERE p.is_active = 1"
        q += " ORDER BY p.label"
        rows = conn.execute(q).fetchall()
        out = []
        for r in rows:
            d = dict(r)
            d["keywords"] = _load_json(d.get("keywords"), []) or []
            out.append(d)
        return out
    finally:
        conn.close()


def get_problem_pattern(pattern_id):
    conn = connect()
    try:
        row = conn.execute(
            "SELECT p.*, s.name AS solution_name, s.slug AS solution_slug"
            " FROM problem_patterns p JOIN solution_templates s ON s.id = p.solution_id"
            " WHERE p.id = ?", (pattern_id,)).fetchone()
        if row is None:
            return None
        d = dict(row)
        d["keywords"] = _load_json(d.get("keywords"), []) or []
        return d
    finally:
        conn.close()


def create_problem_pattern(data):
    conn = connect()
    try:
        sol = conn.execute("SELECT id FROM solution_templates WHERE slug = ?",
                           (data["solution_slug"],)).fetchone()
        if sol is None:
            return None
        cur = conn.execute(
            "INSERT INTO problem_patterns (slug, label, keywords, description, solution_id,"
            " urgency_hint, size_hint, is_active)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (data["slug"], data["label"], json.dumps(data["keywords"]),
             data.get("description"), sol["id"], data.get("urgency_hint"),
             data.get("size_hint"), 1 if data.get("is_active", True) else 0))
        conn.commit()
        return get_problem_pattern(cur.lastrowid)
    finally:
        conn.close()


def update_problem_pattern(pattern_id, fields):
    conn = connect()
    try:
        allowed = {"label", "keywords", "description", "urgency_hint", "size_hint", "is_active"}
        sets = []
        values = []
        for key, value in fields.items():
            if key not in allowed or value is None:
                continue
            if key == "keywords":
                value = json.dumps(value or [])
            elif key == "is_active":
                value = 1 if value else 0
            sets.append(f"{key} = ?")
            values.append(value)
        if fields.get("solution_slug") is not None:
            sol = conn.execute("SELECT id FROM solution_templates WHERE slug = ?",
                               (fields["solution_slug"],)).fetchone()
            if sol is None:
                return None
            sets.append("solution_id = ?")
            values.append(sol["id"])
        if sets:
            sets.append("updated_at = datetime('now')")
            values.append(pattern_id)
            conn.execute(f"UPDATE problem_patterns SET {', '.join(sets)} WHERE id = ?", values)
        conn.commit()
        return get_problem_pattern(pattern_id)
    finally:
        conn.close()


def delete_problem_pattern(pattern_id):
    conn = connect()
    try:
        cur = conn.execute("DELETE FROM problem_patterns WHERE id = ?", (pattern_id,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()