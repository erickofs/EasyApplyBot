import time, random, csv, pyautogui, pdb, traceback, sys
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from datetime import date, datetime
from itertools import product

class LinkedinEasyApply:
    def __init__(self, parameters, driver):
        self.browser = driver
        self.email = parameters['email']
        self.password = parameters['password']
        self.disable_lock = parameters['disableAntiLock']
        self.company_blacklist = parameters.get('companyBlacklist', []) or []
        self.title_blacklist = parameters.get('titleBlacklist', []) or []
        self.poster_blacklist = parameters.get('posterBlacklist', []) or []
        self.positions = parameters.get('positions', [])
        self.locations = parameters.get('locations', [])
        self.residency = parameters.get('residentStatus', [])
        self.base_search_url = self.get_base_search_url(parameters)
        self.seen_jobs = []
        self.file_name = "../output_"
        self.unprepared_questions_file_name = "../unprepared_questions"
        self.output_file_directory = parameters['outputFileDirectory']
        self.resume_dir = parameters['uploads']['resume']
        if 'coverLetter' in parameters['uploads']:
            self.cover_letter_dir = parameters['uploads']['coverLetter']
        else:
            self.cover_letter_dir = ''
        self.checkboxes = parameters.get('checkboxes', [])
        self.university_gpa = parameters['universityGpa']
        self.salary_minimum = parameters['salaryMinimum']
        self.notice_period = int(parameters['noticePeriod'])
        self.languages = parameters.get('languages', [])
        self.experience = parameters.get('experience', [])
        self.personal_info = parameters.get('personalInfo', [])
        self.eeo = parameters.get('eeo', [])
        self.experience_default = int(self.experience['default'])

    def login(self):
        try:
            self.browser.get("https://www.linkedin.com/login")
            time.sleep(random.uniform(5, 10))
            self.browser.find_element(By.ID, "username").send_keys(self.email)
            self.browser.find_element(By.ID, "password").send_keys(self.password)
            self.browser.find_element(By.CSS_SELECTOR, ".btn__primary--large").click()
            time.sleep(random.uniform(5, 10))
        except TimeoutException:
            raise Exception("Could not login!")

    def security_check(self):
        current_url = self.browser.current_url
        page_source = self.browser.page_source

        if '/checkpoint/challenge/' in current_url or 'security check' in page_source:
            input("Please complete the security check and press enter on this console when it is done.")
            time.sleep(random.uniform(5.5, 10.5))

    def start_applying(self):
        searches = list(product(self.positions, self.locations))
        random.shuffle(searches)

        page_sleep = 0
        minimum_time = 60 * 15  # minimum time bot should run before taking a break
        minimum_page_time = time.time() + minimum_time

        for (position, location) in searches:
            location_url = "&location=" + location
            job_page_number = -1

            print("Starting the search for " + position + " in " + location + ".")

            try:
                while True:
                    page_sleep += 1
                    job_page_number += 1
                    print("Going to job page " + str(job_page_number))
                    self.next_job_page(position, location_url, job_page_number)
                    time.sleep(random.uniform(1.5, 3.5))
                    print("Starting the application process for this page...")
                    self.apply_jobs(location)
                    print("Job applications on this page have been successfully completed.")

                    time_left = minimum_page_time - time.time()
                    if time_left > 0:
                        print("Sleeping for " + str(time_left) + " seconds.")
                        time.sleep(time_left)
                        minimum_page_time = time.time() + minimum_time
                    if page_sleep % 5 == 0:
                        sleep_time = random.randint(180, 300)  # Changed from 500, 900 {seconds}
                        print("Sleeping for " + str(sleep_time / 60) + " minutes.")
                        time.sleep(sleep_time)
                        page_sleep += 1
            except:
                traceback.print_exc()
                pass

            time_left = minimum_page_time - time.time()
            if time_left > 0:
                print("Sleeping for " + str(time_left) + " seconds.")
                time.sleep(time_left)
                minimum_page_time = time.time() + minimum_time
            if page_sleep % 5 == 0:
                sleep_time = random.randint(500, 900)
                print("Sleeping for " + str(sleep_time / 60) + " minutes.")
                time.sleep(sleep_time)
                page_sleep += 1

    def apply_jobs(self, location):
        no_jobs_text = ""
        try:
            no_jobs_element = self.browser.find_element(By.CLASS_NAME,
                                                        'jobs-search-two-pane__no-results-banner--expand')
            no_jobs_text = no_jobs_element.text
        except:
            pass
        if 'No matching jobs found' in no_jobs_text:
            raise Exception("No more jobs on this page.")

        if 'unfortunately, things are' in self.browser.page_source.lower():
            raise Exception("No more jobs on this page.")

        job_results_header = ""
        maybe_jobs_crap = ""
        job_results_header = self.browser.find_element(By.CLASS_NAME, "jobs-search-results-list__text")
        maybe_jobs_crap = job_results_header.text

        if 'Jobs you may be interested in' in maybe_jobs_crap:
            raise Exception("Nothing to do here, moving forward...")

        try:
            job_results = self.browser.find_element(By.CLASS_NAME, "jobs-search-results-list")
            self.scroll_slow(job_results)
            self.scroll_slow(job_results, step=300, reverse=True)

            job_list = self.browser.find_elements(By.CLASS_NAME, 'scaffold-layout__list-container')[0].find_elements(
                By.CLASS_NAME, 'jobs-search-results__list-item')
            if len(job_list) == 0:
                raise Exception("No job class elements found in page")
        except:
            raise Exception("No more jobs on this page.")

        if len(job_list) == 0:
            raise Exception("No more jobs on this page.")

        for job_tile in job_list:
            job_title, company, poster, job_location, apply_method, link = "", "", "", "", "", ""

            try:
                job_title = job_tile.find_element(By.CLASS_NAME, 'job-card-list__title').text
                link = job_tile.find_element(By.CLASS_NAME, 'job-card-list__title').get_attribute('href').split('?')[0]
            except:
                pass
            try:
                company = job_tile.find_element(By.CLASS_NAME, 'job-card-container__primary-description').text
            except:
                pass
            try:
                # get the name of the person who posted for the position, if any is listed
                hiring_line = job_tile.find_element(By.XPATH, '//span[contains(.,\' is hiring for this\')]')
                hiring_line_text = hiring_line.text
                name_terminating_index = hiring_line_text.find(' is hiring for this')
                if name_terminating_index != -1:
                    poster = hiring_line_text[:name_terminating_index]
            except:
                pass
            try:
                job_location = job_tile.find_element(By.CLASS_NAME, 'job-card-container__metadata-item').text
            except:
                pass
            try:
                apply_method = job_tile.find_element(By.CLASS_NAME, 'job-card-container__apply-method').text
            except:
                pass

            contains_blacklisted_keywords = False
            job_title_parsed = job_title.lower().split(' ')

            for word in self.title_blacklist:
                if word.lower() in job_title_parsed:
                    contains_blacklisted_keywords = True
                    break

            if company.lower() not in [word.lower() for word in self.company_blacklist] and \
                    poster.lower() not in [word.lower() for word in self.poster_blacklist] and \
                    contains_blacklisted_keywords is False and link not in self.seen_jobs:
                try:
                    max_retries = 3
                    retries = 0
                    while retries < max_retries:
                        try:
                            job_el = job_tile.find_element(By.CLASS_NAME, 'job-card-list__title')
                            job_el.click()
                            break

                        except StaleElementReferenceException:
                            retries += 1
                            continue

                    time.sleep(random.uniform(3, 5))

                    try:
                        done_applying = self.apply_to_job()
                        if done_applying:
                            print(f"Application sent to {company} for the position of {job_title}.")
                        else:
                            print(f"An application for a job at {company} has been submitted earlier.")
                    except:
                        temp = self.file_name
                        self.file_name = "../failed_"
                        print("Failed to apply to job. Please submit a bug report with this link: " + link)
                        try:
                            self.write_to_file(company, job_title, link, job_location, location)
                        except:
                            pass
                        self.file_name = temp

                    try:
                        self.write_to_file(company, job_title, link, job_location, location)
                    except Exception:
                        print(
                            "Unable to save the job information in the file. The job title or company cannot contain special characters,")
                        traceback.print_exc()
                except:
                    traceback.print_exc()
                    print(f"Could not apply to the job in {company}")
                    pass
            else:
                print(f"Job for {company} by {poster} contains a blacklisted word {word}.")

            self.seen_jobs += link

    def apply_to_job(self):
        easy_apply_button = None

        try:
            easy_apply_button = self.browser.find_element(By.CLASS_NAME, 'jobs-apply-button')
        except:
            return False

        try:
            job_description_area = self.browser.find_element(By.CLASS_NAME, "jobs-search__job-details--container")
            self.scroll_slow(job_description_area, end=1600)
            self.scroll_slow(job_description_area, end=1600, step=400, reverse=True)
        except:
            pass

        print("Starting the job application...")
        easy_apply_button.click()

        button_text = ""
        submit_application_text = 'submit application'
        while submit_application_text not in button_text.lower():
            try:
                self.fill_up()
                next_button = self.browser.find_element(By.CLASS_NAME, "artdeco-button--primary")
                button_text = next_button.text.lower()
                if submit_application_text in button_text:
                    try:
                        self.unfollow()
                    except:
                        print("Failed to unfollow company.")
                time.sleep(random.uniform(1.5, 2.5))
                next_button.click()
                time.sleep(random.uniform(3.0, 5.0))

                # Newer error handling
                error_messages = [
                    'enter a valid',
                    'enter a decimal',
                    'file is required',
                    'make a selection',
                    'select checkbox to proceed',
                    'saisissez un numéro',
                    '请输入whole编号',
                    'Numéro de téléphone',
                    'use the format'
                ]

                if any(error in self.browser.page_source.lower() for error in error_messages):
                    raise Exception("Failed answering required questions or uploading required files.")
            except:
                traceback.print_exc()
                self.browser.find_element(By.CLASS_NAME, 'artdeco-modal__dismiss').click()
                time.sleep(random.uniform(3, 5))
                self.browser.find_elements(By.CLASS_NAME, 'artdeco-modal__confirm-dialog-btn')[1].click()
                time.sleep(random.uniform(3, 5))
                raise Exception("Failed to apply to job!")

        closed_notification = False
        time.sleep(random.uniform(3, 5))
        try:
            self.browser.find_element(By.CLASS_NAME, 'artdeco-modal__dismiss').click()
            closed_notification = True
        except:
            pass
        try:
            self.browser.find_element(By.CLASS_NAME, 'artdeco-toast-item__dismiss').click()
            closed_notification = True
        except:
            pass
        try:
            self.browser.find_element(By.CSS_SELECTOR, 'button[data-control-name="save_application_btn"]').click()
            closed_notification = True
        except:
            pass

        time.sleep(random.uniform(3, 5))

        if closed_notification is False:
            raise Exception("Could not close the applied confirmation window!")

        return True

    def home_address(self, element):
        try:
            groups = element.find_elements(By.CLASS_NAME, 'jobs-easy-apply-form-section__grouping')
            if len(groups) > 0:
                for group in groups:
                    lb = group.find_element(By.TAG_NAME, 'label').text.lower()
                    input_field = group.find_element(By.TAG_NAME, 'input')
                    if 'street' in lb:
                        self.enter_text(input_field, self.personal_info['Street address'])
                    elif 'city' in lb:
                        self.enter_text(input_field, self.personal_info['City'])
                        time.sleep(3)
                        input_field.send_keys(Keys.DOWN)
                        input_field.send_keys(Keys.RETURN)
                    elif 'zip' in lb or 'zip / postal code' in lb or 'postal' in lb:
                        self.enter_text(input_field, self.personal_info['Zip'])
                    elif 'state' in lb or 'province' in lb:
                        self.enter_text(input_field, self.personal_info['State'])
                    else:
                        pass
        except:
            pass

    def get_answer(self, question):
        if self.checkboxes[question]:
            return 'yes'
        else:
            return 'no'

    def additional_questions(self):
        # pdb.set_trace()
        frm_el = self.browser.find_elements(By.CLASS_NAME, 'jobs-easy-apply-form-section__grouping')
        if len(frm_el) > 0:
            for el in frm_el:
                # Radio check
                try:
                    question = el.find_element(By.CLASS_NAME, 'jobs-easy-apply-form-element')
                    radios = question.find_elements(By.CLASS_NAME, 'fb-text-selectable__option')
                    if len(radios) == 0:
                        raise Exception("No radio found in element")

                    radio_text = el.text.lower()
                    radio_options = [text.text.lower() for text in radios]
                    answer = "yes"

                    if 'driver\'s licence' in radio_text or 'driver\'s license' in radio_text:
                        answer = self.get_answer('driversLicence')

                    elif any(keyword in radio_text.lower() for keyword in
                             [
                                 'Aboriginal', 'native', 'indigenous', 'tribe', 'first nations',
                                 'native american', 'native hawaiian', 'inuit', 'metis', 'maori',
                                 'aborigine', 'ancestral', 'native peoples', 'original people',
                                 'first people', 'gender', 'race', 'disability', 'latino', 'torres',
                                 'do you identify'
                             ]):
                        negative_keywords = ['prefer', 'decline', 'don\'t', 'specified', 'none', 'no']
                        answer = next((option for option in radio_options if
                                       any(neg_keyword in option.lower() for neg_keyword in negative_keywords)), None)

                    elif 'assessment' in radio_text:
                        answer = self.get_answer("assessment")

                    elif 'clearance' in radio_text:
                        answer = self.get_answer("securityClearance")

                    elif 'north korea' in radio_text:
                        answer = 'no'

                    elif 'previously employ' in radio_text or 'previous employ' in radio_text:
                        answer = 'no'

                    elif 'authorized' in radio_text or 'authorised' in radio_text or 'legally' in radio_text:
                        answer = self.get_answer('legallyAuthorized')

                    elif any(keyword in radio_text.lower() for keyword in
                             ['certified', 'certificate', 'cpa', 'chartered accountant', 'qualification']):
                        answer = self.get_answer('certifiedProfessional')

                    elif 'urgent' in radio_text:
                        answer = self.get_answer('urgentFill')

                    elif 'commut' in radio_text or 'on-site' in radio_text or 'hybrid' in radio_text or 'onsite' in radio_text:
                        answer = self.get_answer('commute')

                    elif 'remote' in radio_text:
                        answer = self.get_answer('remote')

                    elif 'background check' in radio_text:
                        answer = self.get_answer('backgroundCheck')

                    elif 'drug test' in radio_text:
                        answer = self.get_answer('drugTest')

                    elif 'currently living' in radio_text or 'currently reside' in radio_text or 'right to live' in radio_text:
                        answer = self.get_answer('residency')

                    elif 'level of education' in radio_text:
                        for degree in self.checkboxes['degreeCompleted']:
                            if degree.lower() in radio_text:
                                answer = "yes"
                                break

                    elif 'experience' in radio_text:
                        for experience in self.experience:
                            if experience.lower() in radio_text:
                                answer = "yes"
                                break

                    elif 'data retention' in radio_text:
                        answer = 'no'

                    elif 'sponsor' in radio_text:
                        answer = self.get_answer('requireVisa')
                    else:
                        answer = radio_options[len(radio_options) - 1]
                        self.record_unprepared_question("radio", radio_text)

                    i = 0
                    to_select = None
                    for radio in radios:
                        if answer in radio.text.lower():
                            to_select = radios[i]
                        i += 1

                    if to_select is None:
                        to_select = radios[len(radios) - 1]

                    self.radio_select(to_select, answer, len(radios) > 2)

                    if radios != []:
                        continue
                except:
                    pass

                # Questions check
                try:
                    question = el.find_element(By.CLASS_NAME, 'jobs-easy-apply-form-element')
                    question_text = question.find_element(By.TAG_NAME, 'label').text.lower()

                    txt_field_visible = False
                    try:
                        txt_field = question.find_element(By.TAG_NAME, 'input')
                        txt_field_visible = True
                    except:
                        try:
                            txt_field = question.find_element(By.TAG_NAME, 'textarea')  # TODO: Test textarea
                            txt_field_visible = True
                        except:
                            raise Exception("Could not find textarea or input tag for question")

                    text_field_type = txt_field.get_attribute('type').lower()
                    if 'numeric' in text_field_type:  # TODO: test numeric type
                        text_field_type = 'numeric'
                    elif 'text' in text_field_type:
                        text_field_type = 'text'
                    else:
                        raise Exception("Could not determine input type of input field!")

                    to_enter = ''
                    if 'experience' in question_text or 'how many years in' in question_text:
                        no_of_years = None
                        for experience in self.experience:
                            if experience.lower() in question_text:
                                no_of_years = int(self.experience[experience])
                                break
                        if no_of_years is None:
                            self.record_unprepared_question(text_field_type, question_text)
                            no_of_years = int(self.experience_default)
                        to_enter = no_of_years

                    elif 'grade point average' in question_text:
                        to_enter = self.university_gpa

                    elif 'first name' in question_text:
                        to_enter = self.personal_info['First Name']

                    elif 'last name' in question_text:
                        to_enter = self.personal_info['Last Name']

                    elif 'name' in question_text:
                        to_enter = self.personal_info['First Name'] + " " + self.personal_info['Last Name']

                    elif 'pronouns' in question_text:
                        to_enter = self.personal_info['Pronouns']

                    elif 'phone' in question_text:
                        to_enter = self.personal_info['Mobile Phone Number']

                    elif 'linkedin' in question_text:
                        to_enter = self.personal_info['Linkedin']

                    elif 'message to hiring' in question_text or 'cover letter' in question_text:
                        to_enter = self.personal_info['MessageToManager']

                    elif 'website' in question_text or 'github' in question_text or 'portfolio' in question_text:
                        to_enter = self.personal_info['Website']

                    elif 'notice' in question_text or 'weeks' in question_text:
                        if text_field_type == 'numeric':
                            to_enter = int(self.notice_period)
                        else:
                            to_enter = str(self.notice_period)

                    elif 'salary' in question_text or 'expectation' in question_text or 'compensation' in question_text or 'CTC' in question_text:
                        if text_field_type == 'numeric':
                            to_enter = int(self.salary_minimum)
                        else:
                            to_enter = float(self.salary_minimum)
                        self.record_unprepared_question(text_field_type, question_text)

                    if text_field_type == 'numeric':
                        if not isinstance(to_enter, (int, float)):
                            to_enter = 0
                    elif to_enter == '':
                        to_enter = " ‏‏‎ "

                    self.enter_text(txt_field, to_enter)
                    continue
                except:
                    pass

                # Date Check
                try:
                    date_picker = el.find_element(By.CLASS_NAME, 'artdeco-datepicker__input ')
                    date_picker.clear()
                    date_picker.send_keys(date.today().strftime("%m/%d/%y"))
                    time.sleep(3)
                    date_picker.send_keys(Keys.RETURN)
                    time.sleep(2)
                    continue
                except:
                    pass

                # Dropdown check
                try:
                    question = el.find_element(By.CLASS_NAME, 'jobs-easy-apply-form-element')
                    question_text = question.find_element(By.TAG_NAME, 'label').text.lower()
                    dropdown_field = question.find_element(By.TAG_NAME, 'select')

                    select = Select(dropdown_field)
                    options = [options.text for options in select.options]

                    if 'proficiency' in question_text:
                        proficiency = "Conversational"
                        for language in self.languages:
                            if language.lower() in question_text:
                                proficiency = self.languages[language]
                                break
                        self.select_dropdown(dropdown_field, proficiency)

                    elif 'clearance' in question_text:
                        answer = self.get_answer('securityClearance')

                        choice = ""
                        for option in options:
                            if answer == 'yes':
                                choice = option
                            else:
                                if 'no' in option.lower():
                                    choice = option
                        if choice == "":
                            self.record_unprepared_question(text_field_type, question_text)
                        self.select_dropdown(dropdown_field, choice)

                    elif 'assessment' in question_text:
                        answer = self.get_answer('assessment')
                        choice = ""
                        for option in options:
                            if answer == 'yes':
                                choice = option
                            else:
                                if 'no' in option.lower():
                                    choice = option
                        # if choice == "":
                        #    choice = options[len(options) - 1]
                        self.select_dropdown(dropdown_field, choice)

                    elif 'commut' in question_text or 'on-site' in question_text or 'hybrid' in question_text or 'onsite' in question_text:
                        answer = self.get_answer('commute')

                        choice = ""
                        for option in options:
                            if answer == 'yes':
                                choice = option
                            else:
                                if 'no' in option.lower():
                                    choice = option
                        # if choice == "":
                        #    choice = options[len(options) - 1]
                        self.select_dropdown(dropdown_field, choice)

                    elif 'country code' in question_text:
                        self.select_dropdown(dropdown_field, self.personal_info['Phone Country Code'])

                    elif 'north korea' in question_text:
                        choice = ""
                        for option in options:
                            if 'no' in option.lower():
                                choice = option
                        if choice == "":
                            choice = options[len(options) - 1]
                        self.select_dropdown(dropdown_field, choice)

                    elif 'previously employed' in question_text or 'previous employment' in question_text:
                        choice = ""
                        for option in options:
                            if 'no' in option.lower():
                                choice = option
                        if choice == "":
                            choice = options[len(options) - 1]
                        self.select_dropdown(dropdown_field, choice)

                    elif 'sponsor' in question_text:
                        answer = self.get_answer('requireVisa')
                        choice = ""
                        for option in options:
                            if answer == 'yes':
                                choice = option
                            else:
                                if 'no' in option.lower():
                                    choice = option
                        if choice == "":
                            choice = options[len(options) - 1]
                        self.select_dropdown(dropdown_field, choice)

                    elif 'currently living' in question_text or 'currently reside' in question_text:
                        answer = self.get_answer('residency')
                        choice = ""
                        for option in options:
                            if answer == 'yes':
                                choice = option
                            else:
                                if 'no' in option.lower():
                                    choice = option
                        if choice == "":
                            choice = options[len(options) - 1]
                        self.select_dropdown(dropdown_field, choice)

                    elif 'authorized' in question_text or 'authorised' in question_text:
                        answer = self.get_answer('legallyAuthorized')
                        choice = ""
                        for option in options:
                            if answer == 'yes':
                                # find some common words
                                choice = option
                            else:
                                if 'no' in option.lower():
                                    choice = option
                        if choice == "":
                            choice = options[len(options) - 1]
                        self.select_dropdown(dropdown_field, choice)

                    elif 'citizenship' in question_text:
                        answer = self.get_answer('legallyAuthorized')
                        choice = ""
                        for option in options:
                            if answer == 'yes':
                                if 'no' in option.lower():
                                    choice = option
                        if choice == "":
                            choice = options[len(options) - 1]
                        self.select_dropdown(dropdown_field, choice)

                    elif 'clearance' in question_text:
                        answer = self.get_answer('clearance')
                        choice = ""
                        for option in options:
                            if answer == 'yes':
                                choice = option
                            else:
                                if 'no' in option.lower():
                                    choice = option
                        if choice == "":
                            choice = options[len(options) - 1]

                        self.select_dropdown(dropdown_field, choice)

                    elif any(keyword in question_text.lower() for keyword in
                             [
                                 'aboriginal', 'native', 'indigenous', 'tribe', 'first nations',
                                 'native american', 'native hawaiian', 'inuit', 'metis', 'maori',
                                 'aborigine', 'ancestral', 'native peoples', 'original people',
                                 'first people', 'gender', 'race', 'disability', 'latino'
                             ]):
                        negative_keywords = ['prefer', 'decline', 'don\'t', 'specified', 'none']

                        choice = ""
                        choice = next((option for options in option.lower() if
                                   any(neg_keyword in option.lower() for neg_keyword in negative_keywords)), None)

                        self.select_dropdown(dropdown_field, choice)

                    elif 'email' in question_text:
                        continue  # assume email address is filled in properly by default

                    elif 'experience' in question_text or 'understanding' in question_text or 'familiar' in question_text or 'comfortable' in question_text or 'able to' in question_text:
                        answer = 'no'
                        for experience in self.experience:
                            if experience.lower() in question_text and self.experience[experience] > 0:
                                answer = 'yes'
                                break
                        if answer == 'no':
                            # record unlisted experience as unprepared questions
                            self.record_unprepared_question("dropdown", question_text)

                        choice = ""
                        for option in options:
                            if answer in option.lower():
                                choice = option
                        if choice == "":
                            choice = options[len(options) - 1]
                        self.select_dropdown(dropdown_field, choice)

                    else:
                        choice = ""
                        for option in options:
                            if 'yes' in option.lower():
                                choice = option
                        if choice == "":
                            choice = options[len(options) - 1]
                        self.select_dropdown(dropdown_field, choice)
                        self.record_unprepared_question("dropdown", question_text)
                    continue
                except:
                    pass

                # Checkbox check for agreeing to terms and service
                try:
                    question = el.find_element(By.CLASS_NAME, 'jobs-easy-apply-form-element')
                    clickable_checkbox = question.find_element(By.TAG_NAME, 'label')
                    clickable_checkbox.click()
                except:
                    pass

    def unfollow(self):
        try:
            follow_checkbox = self.browser.find_element(By.XPATH,
                                                        "//label[contains(.,\'to stay up to date with their page.\')]").click()
            follow_checkbox.click()
        except:
            pass

    def send_resume(self):
        try:
            file_upload_elements = (By.CSS_SELECTOR, "input[name='file']")
            if len(self.browser.find_elements(file_upload_elements[0], file_upload_elements[1])) > 0:
                input_buttons = self.browser.find_elements(file_upload_elements[0], file_upload_elements[1])
                if len(input_buttons) == 0:
                    raise Exception("No input elements found in element")
                for upload_button in input_buttons:
                    upload_type = upload_button.find_element(By.XPATH, "..").find_element(By.XPATH,
                                                                                          "preceding-sibling::*")
                    if 'resume' in upload_type.text.lower():
                        upload_button.send_keys(self.resume_dir)
                    elif 'cover' in upload_type.text.lower():
                        if self.cover_letter_dir != '':
                            upload_button.send_keys(self.cover_letter_dir)
                        elif 'required' in upload_type.text.lower():
                            upload_button.send_keys(self.resume_dir)
        except:
            # print("Failed to upload resume or cover letter!")
            pass

    def enter_text(self, element, text):
        element.clear()
        element.send_keys(text)

    def select_dropdown(self, element, text):
        select = Select(element)
        select.select_by_visible_text(text)

    # Radio Select
    def radio_select(self, element, label_text, clickLast=False):
        label = element.find_element(By.TAG_NAME, 'label')
        if label_text in label.text.lower() or clickLast == True:
            label.click()
        else:
            pass

    # Contact info fill-up
    def contact_info(self):
        frm_el = self.browser.find_elements(By.CLASS_NAME, 'jobs-easy-apply-form-section__grouping')
        if len(frm_el) > 0:
            for el in frm_el:
                text = el.text.lower()
                if 'email address' in text:
                    continue
                elif 'phone number' in text:
                    try:
                        country_code_picker = el.find_element(By.XPATH,
                                                              '//select[contains(@id,"phoneNumber")][contains(@id,"country")]')
                        self.select_dropdown(country_code_picker, self.personal_info['Phone Country Code'])
                    except Exception as e:
                        print("Country code " + self.personal_info[
                            'Phone Country Code'] + " not found. Please make sure it is same as in LinkedIn.")
                        print(e)
                    try:
                        phone_number_field = el.find_element(By.XPATH,
                                                             '//input[contains(@id,"phoneNumber")][contains(@id,"nationalNumber")]')
                        self.enter_text(phone_number_field, self.personal_info['Mobile Phone Number'])
                    except Exception as e:
                        print("Could not enter phone number:")
                        print(e)

    def fill_up(self):
        try:
            easy_apply_content = self.browser.find_element(By.CLASS_NAME, 'jobs-easy-apply-content')
            b4 = easy_apply_content.find_element(By.CLASS_NAME, 'pb4')
            pb4 = easy_apply_content.find_elements(By.CLASS_NAME, 'pb4')
            if len(pb4) == 0:
                raise Exception("No pb4 class elements found in element")
            if len(pb4) > 0:
                for pb in pb4:
                    try:
                        label = pb.find_element(By.TAG_NAME, 'h3').text.lower()
                        try:
                            self.additional_questions()
                        except:
                            pass

                        try:
                            self.send_resume()
                        except:
                            pass

                        if 'home address' in label:
                            self.home_address(pb)
                        elif 'contact info' in label:
                            self.contact_info()
                    except:
                        pass
        except:
            pass

    def write_to_file(self, company, job_title, link, location, search_location):
        to_write = [company, job_title, link, location, datetime.now()]
        # file_path = self.output_file_directory + self.file_name + search_location + ".csv"
        file_path = self.file_name + search_location + ".csv"

        with open(file_path, 'a') as f:
            writer = csv.writer(f)
            writer.writerow(to_write)

    def record_unprepared_question(self, answer_type, question_text):
        to_write = [answer_type, question_text]
        file_path = self.unprepared_questions_file_name + ".csv"

        try:
            with open(file_path, 'a') as f:
                writer = csv.writer(f)
                writer.writerow(to_write)
        except:
            print(
                "Special characters in questions are not allowed. Failed to update unprepared questions log.")
            print(question_text)

    def scroll_slow(self, scrollable_element, start=0, end=3600, step=100, reverse=False):
        if reverse:
            start, end = end, start
            step = -step

        for i in range(start, end, step):
            self.browser.execute_script("arguments[0].scrollTo(0, {})".format(i), scrollable_element)
            time.sleep(random.uniform(1.0, 2.6))

    def avoid_lock(self):
        if self.disable_lock:
            return

        pyautogui.keyDown('ctrl')
        pyautogui.press('esc')
        pyautogui.keyUp('ctrl')
        time.sleep(1.0)
        pyautogui.press('esc')

    def get_base_search_url(self, parameters):
        remote_url = ""
        lessthanTenApplicants_url = ""

        if parameters.get('remote'):
            remote_url = "&f_WT=2"
        else:
            remote_url = ""
            # TO DO: Others &f_WT= options { WT=1 onsite, WT=2 remote, WT=3 hybrid, f_WT=1%2C2%2C3 }

        if parameters['lessthanTenApplicants']:
            lessthanTenApplicants_url = "&f_EA=true"

        level = 1
        experience_level = parameters.get('experienceLevel', [])
        experience_url = "f_E="
        for key in experience_level.keys():
            if experience_level[key]:
                experience_url += "%2C" + str(level)
            level += 1

        distance_url = "?distance=" + str(parameters['distance'])

        job_types_url = "f_JT="
        job_types = parameters.get('experienceLevel', [])
        for key in job_types:
            if job_types[key]:
                job_types_url += "%2C" + key[0].upper()

        date_url = ""
        dates = {"all time": "", "month": "&f_TPR=r2592000", "week": "&f_TPR=r604800", "24 hours": "&f_TPR=r86400"}
        date_table = parameters.get('date', [])
        for key in date_table.keys():
            if date_table[key]:
                date_url = dates[key]
                break

        easy_apply_url = "&f_AL=true"

        extra_search_terms = [distance_url, remote_url, lessthanTenApplicants_url, job_types_url, experience_url]
        extra_search_terms_str = '&'.join(
            term for term in extra_search_terms if len(term) > 0) + easy_apply_url + date_url

        return extra_search_terms_str

    def next_job_page(self, position, location, job_page):
        self.browser.get("https://www.linkedin.com/jobs/search/" + self.base_search_url +
                         "&keywords=" + position + location + "&start=" + str(job_page * 25))

        self.avoid_lock()
