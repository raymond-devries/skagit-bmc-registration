from datetime import datetime
import django

django.setup()

from registration import models  # noqa E402

if __name__ == "__main__":
    course_dates_data = """Required Fitness Hike: Sat Mar 15 2025
    First Class Session, Burlington: Wed Mar 26 2025
    Navigation Outing: Sat Mar 29 2025
    Navigation Outing (Rain Backup): Sun Mar 30 2025
    Trail work party day placeholder: Sat Apr 05 2025
    Class Session in Burlington: Wed Apr 9 2025
    Ice Axe Arrest Outing: Sat Apr 12, 2025 - Apr 13, 2025
    Class Session in Burlington: Wed Apr 16, 2025
    Rock Climbing Intro Outing: Sat Apr 19, 2025
    Rock Climbing Intro Outing (Rain Backup): Sun Apr 20, 2025
    Class Session in Burlington: Wed Apr 23, 2025
    Rope Team Travel Outing: Sat Apr 26, 2025 - Apr 27, 2025
    Class Session in Burlington: Wed Apr 30, 2025
    Lead Belay Outing: Sat May 03, 2025 - May 04, 2025
    Trail work party day placeholder 2: Sat May 10, 2025
    Class Session in Burlington: Wed May 14, 2025
    Crevasse Rescue outing: Sat May 17 2025 - May 18, 2025
    (Optional) Skagit Alpine Club Group Camp: Fri May 24 2025 - May 26, 2025
    Class Session in Burlington: Wed Jun 04, 2025
    Crevasse Rescue 2 Outing: Sat Jun 07 2025 - Jun 8, 2025"""

    course_dates_data = course_dates_data.split("\n")

    def parse_date_range(date_str):
        date_str = date_str.replace(",", "")
        if "-" in date_str:  # Check if it's a date range
            parts = date_str.split("-")
            start_date_str = parts[0].strip()
            end_date_str = parts[1].strip()
            # Check if the end date includes the month; if not, infer it
            if len(end_date_str.split()) == 1:
                # Extract the month and year from the start date
                month_year = " ".join(start_date_str.split()[1:3])
                end_date_str = f"{end_date_str} {month_year}"
            # Parse the start and end dates
            start_date = datetime.strptime(start_date_str, "%a %b %d %Y")
            end_date = datetime.strptime(end_date_str, "%b %d %Y")
        else:  # Single date, start and end are the same
            start_date = end_date = datetime.strptime(date_str.strip(), "%a %b %d %Y")
        return start_date, end_date

    course = models.Course.objects.get()
    course.specifics = "BMC 2025"
    course.save()
    course.participants.set([])

    models.WaitList.objects.all().delete()
    models.CourseDate.objects.all().delete()

    for course_date_data in course_dates_data:
        name, dates = course_date_data.split(":")
        start, end = parse_date_range(dates)
        start = start.replace(hour=8)
        end = end.replace(hour=8)
        models.CourseDate.objects.create(name=name, start=start, end=end, course=course)
