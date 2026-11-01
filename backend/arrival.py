"""Personal preparation suggestions, deliberately separate from official requirements."""
from .planner import validate_task


def arrival_tasks(profile, school):
    if not isinstance(profile, dict) or set(profile) - {"arrival_date", "live_on_campus", "need_aid", "long_distance"}:
        raise ValueError("报到偏好格式无效。")
    for key in ("live_on_campus", "need_aid", "long_distance"):
        if type(profile.get(key, False)) is not bool:
            raise ValueError("报到偏好请选择是或否。")
    rows = [("notice", "核对当年入学须知与本人报到安排", "通过学校官方通知确认日期、校区、材料与缴费渠道。"),
            ("identity", "按本人入学须知整理证件材料", "不预设照片数量、材料规格或强制办理事项。")]
    if profile.get("live_on_campus"):
        rows.append(("dorm", "确认宿舍分配与生活用品", "先确认楼栋、床品规格及是否提供，不据参考图预订床位。"))
    if profile.get("need_aid"):
        rows.append(("aid", "向学校核对资助或绿色通道办理方式", "这是自选提醒，不代表资格审核或办理成功；不收集家庭证明。"))
    if profile.get("long_distance"):
        rows.append(("travel", "核对交通与到校路线并预留时间", "不承诺存在接站；校内路线以现场指引为准。"))
    tasks = []
    for identity, title, note in rows:
        task = validate_task({"title": title, "due": profile.get("arrival_date", ""), "priority": "high" if identity == "notice" else "normal",
                              "notes": "个人准备建议，非学校报到规定。" + note + " 学校：" + school["name"]}, {})
        tasks.append({**task, "arrival_template": identity})
    return tasks
