from collections import UserDict
from datetime import datetime, timedelta
import pickle


# -- Класи полів --
class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class Name(Field):
    pass


class Phone(Field):
    def __init__(self, value):
        self.validate(value)
        super().__init__(value)

    @staticmethod
    def validate(value):
        if not value.isdigit() or len(value) != 10:
            raise ValueError("Phone number must contain exactly 10 digits")


class Birthday(Field):
    def __init__(self, value):
        try:
            date_obj = datetime.strptime(value, "%d.%m.%Y")
            super().__init__(date_obj)
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")

    def __str__(self):
        return self.value.strftime("%d.%m.%Y")


# -- Клас Record --
class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone_value):
        phone = Phone(phone_value)
        self.phones.append(phone)

    def remove_phone(self, phone_value):
        self.phones = [p for p in self.phones if p.value != phone_value]

    def edit_phone(self, old_value, new_value):
        for phone in self.phones:
            if phone.value == old_value:
                Phone.validate(new_value)
                phone.value = new_value
                return
        raise ValueError("Old number not found")

    def find_phone(self, phone_value):
        for phone in self.phones:
            if phone.value == phone_value:
                return phone
        return None

    def add_birthday(self, birthday_value):
        self.birthday = Birthday(birthday_value)

    def __str__(self):
        phones = "; ".join(p.value for p in self.phones)
        bday = f", birthday: {self.birthday}" if self.birthday else ""
        return f"Contact name: {self.name.value}, phones: {phones}{bday}"


# -- Клас AddressBook --
class AddressBook(UserDict):
    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name)

    def delete(self, name):
        if name in self.data:
            del self.data[name]

    def get_upcoming_birthdays(self):
        today = datetime.today().date()
        upcoming = []

        for record in self.data.values():
            if record.birthday:
                bday_date = record.birthday.value.date().replace(year=today.year)
                if bday_date < today:
                    bday_date = bday_date.replace(year=today.year + 1)
                delta_days = (bday_date - today).days

                if 0 <= delta_days < 7:
                    if bday_date.weekday() >= 5:
                        bday_date += timedelta(days=(7 - bday_date.weekday()))
                    upcoming.append({
                        "name": record.name.value,
                        "congratulation_date": bday_date.strftime("%d.%m.%Y")
                    })
        return upcoming

    def __str__(self):
        if not self.data:
            return "Address book is empty."
        return "\n".join(str(record) for record in self.data.values())


# -- Збереження/завантаження --
def save_data(book, filename="addressbook.pkl"):
    with open(filename, "wb") as f:
        pickle.dump(book, f)


def load_data(filename="addressbook.pkl"):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        print("Address book file not found. Creating a new one...")
        return AddressBook()


# -- Декоратор для обробки помилок --
def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            return f"Value error: {e}"
        except IndexError:
            return "Not enough arguments provided."
        except KeyError:
            return "Contact not found."
        except Exception as e:
            return f"Error: {e}"
    return inner


# -- Обробники команд --
@input_error
def add_contact(args, book: AddressBook):
    name, phone, *_ = args
    record = book.find(name)
    message = "Contact updated."
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    if phone:
        record.add_phone(phone)
    return message


@input_error
def change_phone(args, book: AddressBook):
    name, old_phone, new_phone = args
    record = book.find(name)
    if record is None:
        raise KeyError
    record.edit_phone(old_phone, new_phone)
    return f"Phone number updated for {name}."


@input_error
def show_phones(args, book: AddressBook):
    name = args[0]
    record = book.find(name)
    if record is None:
        raise KeyError
    phones = "; ".join(p.value for p in record.phones)
    return f"{name}: {phones}"


@input_error
def show_all(args, book: AddressBook):
    return str(book)


@input_error
def add_birthday(args, book: AddressBook):
    name, date = args
    record = book.find(name)
    if record is None:
        raise KeyError
    record.add_birthday(date)
    return f"Birthday added for {name}."


@input_error
def show_birthday(args, book: AddressBook):
    name = args[0]
    record = book.find(name)
    if record is None:
        raise KeyError
    if record.birthday:
        return f"{name}'s birthday is on {record.birthday}"
    return f"No birthday set for {name}."


@input_error
def birthdays(args, book: AddressBook):
    upcoming = book.get_upcoming_birthdays()
    if not upcoming:
        return "No birthdays in the next 7 days."
    lines = [f"{u['name']} - {u['congratulation_date']}" for u in upcoming]
    return "Upcoming birthdays:\n" + "\n".join(lines)


# -- Службова функція --
def parse_input(user_input: str):
    parts = user_input.strip().split()
    command = parts[0].lower() if parts else ""
    args = parts[1:]
    return command, args


# -- Основна функція --
def main():
    book = load_data()
    print("Welcome to the assistant bot!")

    while True:
        user_input = input("Enter a command: ")
        command, args = parse_input(user_input)

        if command in ["close", "exit"]:
            save_data(book)
            print("Data saved. Good bye!")
            break

        elif command == "hello":
            print("How can I help you?")

        elif command == "add":
            print(add_contact(args, book))

        elif command == "change":
            print(change_phone(args, book))

        elif command == "phone":
            print(show_phones(args, book))

        elif command == "all":
            print(show_all(args, book))

        elif command == "add-birthday":
            print(add_birthday(args, book))

        elif command == "show-birthday":
            print(show_birthday(args, book))

        elif command == "birthdays":
            print(birthdays(args, book))

        else:
            print("Invalid command.")


if __name__ == "__main__":
    main()